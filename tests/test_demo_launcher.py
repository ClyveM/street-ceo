"""Launcher dry-run safety with mocked OS inventory; never starts a service."""
import base64
import json
from pathlib import Path
import shutil
import subprocess
import unittest


SHELL = shutil.which("powershell") or shutil.which("pwsh")
SCRIPT = Path(__file__).resolve().parents[1] / "infra" / "start-demo.ps1"


@unittest.skipUnless(SHELL, "PowerShell is required for launcher behavior checks")
class DemoLauncherTests(unittest.TestCase):
    def run_script(self, inventory, check_only=True, serve_apk=True):
        command = """
$ErrorActionPreference = 'Stop'
function global:Start-Process { throw 'Dry run attempted to start a process' }
function global:New-Item { throw 'Dry run attempted to create a directory' }
function global:Set-Content { throw 'Dry run attempted to write a file' }
function global:Invoke-RestMethod { throw 'Synthetic service unavailable' }
function global:netstat.exe { $global:LASTEXITCODE=0; 'Active Connections'; 'Proto Local Address Foreign Address State PID' }
""" + inventory + "\n& '" + str(SCRIPT).replace("'", "''") + "' " + ("-CheckOnly " if check_only else "") + "-LanAddress 192.168.10.213 " + ("-ServeApk " if serve_apk else "") + "| ConvertTo-Json -Compress"
        encoded = base64.b64encode(command.encode("utf-16-le")).decode("ascii")
        return subprocess.run([SHELL, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                              capture_output=True, text=True, timeout=20)

    def test_check_only_reports_existing_listener_without_writes_or_process_start(self):
        result = self.run_script("function global:Get-NetTCPConnection { [pscustomobject]@{ LocalPort=8001; OwningProcess=42; State='Listen' } }")
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["ApiListenerPresent"])
        self.assertFalse(report["DownloadListenerPresent"])
        self.assertEqual(8001, report["ApiPort"])
        self.assertTrue(report["Mode"].startswith("CheckOnly"))

    def test_stale_cim_zero_owner_requires_netstat_nonlistener_corroboration(self):
        result = self.run_script("""
function global:Get-NetTCPConnection { [pscustomobject]@{ LocalPort=8001; OwningProcess=0; State='Listen' } }
function global:netstat.exe { $global:LASTEXITCODE=0; 'TCP 127.0.0.1:8001 127.0.0.1:55000 TIME_WAIT 0'; 'TCP 127.0.0.1:8001 127.0.0.1:55001 FIN_WAIT_1 0' }
""")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(json.loads(result.stdout)["ApiListenerPresent"])

    def test_zero_owner_without_corroboration_or_with_netstat_listen_fails_closed(self):
        for row in ("'Active Connections'", "'TCP 0.0.0.0:8001 0.0.0.0:0 LISTENING 0'"):
            result = self.run_script("""
function global:Get-NetTCPConnection { [pscustomobject]@{ LocalPort=8001; OwningProcess=0; State='Listen' } }
function global:netstat.exe { $global:LASTEXITCODE=0; """ + row + " }")
            self.assertNotEqual(0, result.returncode)
            self.assertIn("unverified zero-owner listener", result.stderr)

    def test_stale_zero_owner_does_not_remove_a_real_nonzero_listener(self):
        result = self.run_script("""
function global:Get-NetTCPConnection { [pscustomobject]@{ LocalPort=8001; OwningProcess=0; State='Listen' }; [pscustomobject]@{ LocalPort=8001; OwningProcess=42; State='Listen' } }
function global:netstat.exe { $global:LASTEXITCODE=0; 'TCP 127.0.0.1:8001 127.0.0.1:55000 TIME_WAIT 0'; 'TCP 0.0.0.0:8001 0.0.0.0:0 LISTENING 42' }
""")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ApiListenerPresent"])

    def test_inventory_denial_fails_closed_instead_of_claiming_a_free_port(self):
        result = self.run_script("function global:Get-NetTCPConnection { throw 'Synthetic inventory denial' }")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("Synthetic inventory denial", result.stderr)
        self.assertNotIn("Dry run attempted", result.stderr)

    def test_start_refuses_unknown_occupied_port_without_starting_or_stopping_it(self):
        result = self.run_script("""
function global:New-Item { }
function global:Get-NetTCPConnection { [pscustomobject]@{ LocalPort=8001; OwningProcess=42; State='Listen' } }
function global:Get-CimInstance { [pscustomobject]@{ CommandLine='some-other-application.exe' } }
function global:Stop-Process { throw 'Unknown process was stopped' }
""", check_only=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("could not prove", result.stderr)
        self.assertNotIn("Dry run attempted", result.stderr)
        self.assertNotIn("Unknown process was stopped", result.stderr)

    def test_empty_cim_does_not_hide_ipv4_or_ipv6_netstat_listener(self):
        for endpoint in ("0.0.0.0:8001 0.0.0.0:0", "[::]:8001 [::]:0"):
            with self.subTest(endpoint=endpoint):
                result = self.run_script("""
function global:Get-NetTCPConnection { }
function global:netstat.exe { $global:LASTEXITCODE=0; 'TCP """ + endpoint + """ LISTENING 30460' }
""")
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertTrue(json.loads(result.stdout)["ApiListenerPresent"])

    def test_empty_cim_netstat_occupied_unknown_owner_is_preserved(self):
        result = self.run_script("""
function global:New-Item { }
function global:Get-NetTCPConnection { }
function global:netstat.exe { $global:LASTEXITCODE=0; 'TCP 0.0.0.0:8001 0.0.0.0:0 LISTENING 30460' }
function global:Get-CimInstance { [pscustomobject]@{ CommandLine='unknown.exe' } }
""", check_only=False)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("could not prove", result.stderr)
        self.assertNotIn("Dry run attempted", result.stderr)

    def test_full_netstat_table_keeps_numbered_nonlistener_states_and_headers(self):
        result = self.run_script("""
function global:Get-NetTCPConnection { }
function global:netstat.exe {
    $global:LASTEXITCODE=0
    'Active Connections'
    'Proto Local Address Foreign Address State PID'
    'TCP 0.0.0.0:445 0.0.0.0:0 CLOSED 4'
    'TCP 0.0.0.0:8081 0.0.0.0:0 CLOSED 4'
    'TCP 192.168.10.213:53321 203.0.113.1:443 FIN_WAIT_2 1234'
    'TCP 192.168.10.213:53322 203.0.113.1:443 FIN_WAIT_1 1234'
    'TCP 0.0.0.0:8001 0.0.0.0:0 LISTENING 30460'
    'TCP [::1]:53323 [::1]:53324 ESTABLISHED 1234'
}
""")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ApiListenerPresent"])
        self.assertFalse(json.loads(result.stdout)["DownloadListenerPresent"])

    def test_empty_cim_netstat_known_owner_reuses_only_verified_runtime(self):
        result = self.run_script("""
function global:New-Item { }
function global:Set-Content { }
function global:Get-NetTCPConnection { }
function global:netstat.exe { $global:LASTEXITCODE=0; 'TCP 0.0.0.0:445 0.0.0.0:0 CLOSED 4'; 'TCP 0.0.0.0:8001 0.0.0.0:0 LISTENING 30460' }
function global:Get-CimInstance { [pscustomobject]@{ CommandLine='python -m uvicorn services.api.app:app --port 8001' } }
function global:Invoke-RestMethod {
    param($Uri, $TimeoutSec)
    if ($Uri.EndsWith('/readyz')) { return [pscustomobject]@{status='ready'} }
    return [pscustomobject]@{store_backend='sqlite';database_identity=(Get-DatabaseIdentity);process_id=30460}
}
""", check_only=False, serve_apk=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("API ready", result.stdout)
        self.assertNotIn("Dry run attempted", result.stderr)

    def test_netstat_error_empty_or_malformed_output_cannot_authorize_start(self):
        for output in ("$global:LASTEXITCODE=1; 'Access denied'", "$global:LASTEXITCODE=0", "$global:LASTEXITCODE=0; 'TCP bad table'", "$global:LASTEXITCODE=0; 'TCP 0.0.0.0:8001 0.0.0.0:0 INVALID 30460'"):
            with self.subTest(output=output):
                result = self.run_script("function global:Get-NetTCPConnection { }; function global:netstat.exe { " + output + " }")
                self.assertNotEqual(0, result.returncode)
                self.assertIn("TCP inventory", result.stderr)
                self.assertNotIn("Dry run attempted", result.stderr)
                self.assertNotIn("0.0.0.0", result.stderr)

    def test_cim_closed_download_row_does_not_become_a_second_listener_owner(self):
        result = self.run_script("""
function global:New-Item { }
function global:Set-Content { }
function global:Test-Path { return $true }
function global:Get-FileHash { [pscustomobject]@{Hash=('a' * 64)} }
function global:Get-NetTCPConnection {
    [pscustomobject]@{LocalPort=8001;OwningProcess=30460;State='Listen'}
    [pscustomobject]@{LocalPort=8081;OwningProcess=25844;State='Closed'}
}
function global:netstat.exe {
    $global:LASTEXITCODE=0
    'TCP 0.0.0.0:8001 0.0.0.0:0 LISTENING 30460'
    'TCP 0.0.0.0:8081 0.0.0.0:0 CLOSED 25844'
    'TCP 0.0.0.0:8081 0.0.0.0:0 LISTENING 16136'
}
function global:Get-CimInstance {
    param($ClassName,$Filter)
    if ($Filter.EndsWith('30460')) { return [pscustomobject]@{CommandLine='python -m uvicorn services.api.app:app --port 8001'} }
    if ($Filter.EndsWith('16136')) { return [pscustomobject]@{CommandLine=('python "' + (Join-Path $Repository 'infra\\serve_apk.py') + '" --apk "' + $Apk + '"')} }
    throw 'A nonlistening process was treated as a listener owner'
}
function global:Invoke-RestMethod {
    param($Uri,$TimeoutSec)
    if ($Uri.EndsWith('/artifact.json')) { return [pscustomobject]@{service='street-ceo-apk-only';sha256=('a' * 64)} }
    if ($Uri.EndsWith('/readyz')) { return [pscustomobject]@{status='ready'} }
    return [pscustomobject]@{store_backend='sqlite';database_identity=(Get-DatabaseIdentity);process_id=30460}
}
""", check_only=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("APK download", result.stdout)
        self.assertNotIn("Dry run attempted", result.stderr)

    def test_empty_both_inventories_reuses_only_live_identity_with_matching_recorded_state(self):
        fixture = """
function global:New-Item { }
function global:Set-Content { }
function global:Get-NetTCPConnection { }
function global:Test-Path { return $true }
function global:Get-Content { param($LiteralPath,[switch]$Raw); return (@{api_process_id=REPLACE_PID;database_identity=(Get-DatabaseIdentity)} | ConvertTo-Json -Compress) }
function global:Get-CimInstance { [pscustomobject]@{CommandLine='python -m uvicorn services.api.app:app --port 8001'} }
function global:Invoke-RestMethod {
    param($Uri,$TimeoutSec)
    if ($Uri.EndsWith('/readyz')) { return [pscustomobject]@{status='ready'} }
    return [pscustomobject]@{store_backend='sqlite';database_identity=(Get-DatabaseIdentity);process_id=30460}
}
"""
        matched = self.run_script(fixture.replace("REPLACE_PID", "30460"), check_only=False, serve_apk=False)
        self.assertEqual(0, matched.returncode, matched.stderr)
        self.assertIn("API ready", matched.stdout)
        self.assertNotIn("Dry run attempted", matched.stderr)
        mismatched = self.run_script(fixture.replace("REPLACE_PID", "999"), check_only=False, serve_apk=False)
        self.assertNotEqual(0, mismatched.returncode)
        self.assertIn("no matching trusted launcher state", mismatched.stderr)
        self.assertNotIn("Dry run attempted", mismatched.stderr)
        unknown_command = self.run_script(fixture.replace("REPLACE_PID", "30460").replace("python -m uvicorn services.api.app:app --port 8001", "unrecognized-service.exe"), check_only=False, serve_apk=False)
        self.assertNotEqual(0, unknown_command.returncode)
        self.assertIn("unrecognized process", unknown_command.stderr)
        self.assertNotIn("Dry run attempted", unknown_command.stderr)


if __name__ == "__main__":
    unittest.main()
