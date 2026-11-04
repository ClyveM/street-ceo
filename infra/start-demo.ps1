[CmdletBinding()]
param(
    [string]$LanAddress = '127.0.0.1',
    [string]$PythonExecutable = 'python',
    [switch]$ServeApk,
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'
$Repository = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$DataDirectory = Join-Path $Repository 'data'
$Database = Join-Path $DataDirectory 'demo-mvp.sqlite3'
if ($env:STREET_CEO_SQLITE_PATH) {
    $Database = $env:STREET_CEO_SQLITE_PATH
    if (-not [System.IO.Path]::IsPathRooted($Database)) {
        $Database = Join-Path $Repository $Database
    }
    $Database = [System.IO.Path]::GetFullPath($Database)
}
$TraceDatabase = Join-Path $DataDirectory 'muse-traces.sqlite3'
$StateFile = Join-Path $DataDirectory 'demo-launcher-state.json'
$Apk = Join-Path $Repository 'apps\android\android\app\build\outputs\apk\debug\app-debug.apk'
$ApiPort = 8001
$DownloadPort = 8081
$PythonPath = (Get-Command $PythonExecutable -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$ParsedAddress = $null
if (-not [System.Net.IPAddress]::TryParse($LanAddress, [ref]$ParsedAddress) -or
    $ParsedAddress.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) {
    throw 'LanAddress must be an IPv4 address of this computer, for example -LanAddress 192.168.10.213.'
}

function Get-Listeners([int]$Port) {
    # CIM can return an incomplete table without an error. Cross-check netstat;
    # neither an empty CIM result nor a failed/malformed query proves a free port.
    $CimListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -eq $Port -and [string]$_.State -eq 'Listen' })
    $NetstatOutput = @(& netstat.exe -ano -p tcp)
    if ($LASTEXITCODE -ne 0) { throw 'TCP inventory failed: netstat exited unsuccessfully. All listeners were preserved.' }
    $NetstatListeners = @()
    $ZeroOwnerNonListener = $false
    $RecognizedOutput = $false
    $ValidStates = @('CLOSED', 'LISTENING', 'ESTABLISHED', 'TIME_WAIT', 'CLOSE_WAIT', 'FIN_WAIT_1', 'FIN_WAIT_2', 'CLOSING', 'SYN_SENT', 'SYN_RECEIVED', 'SYN_RCVD', 'LAST_ACK', 'DELETE_TCB', 'BOUND')
    foreach ($Line in $NetstatOutput) {
        $Text = ([string]$Line).Trim()
        if (-not $Text) { continue }
        if ($Text -eq 'Active Connections' -or $Text -match '^Proto\s+Local Address\s+Foreign Address\s+State\s+PID$') {
            $RecognizedOutput = $true; continue
        }
        if ($Text -notmatch '^TCP\s+(\S+):(\d+)\s+(\S+):(\d+)\s+([A-Z0-9_]+)\s+(\d+)$') {
            throw 'TCP inventory returned malformed or unrecognized output. All listeners were preserved.'
        }
        $LocalEndpoint = $Matches[1]; $LocalPort = [long]$Matches[2]
        $RemoteEndpoint = $Matches[3]; $RemotePort = [long]$Matches[4]
        $TcpState = $Matches[5]; $Owner = [long]$Matches[6]
        $LocalIp = $null; $RemoteIp = $null
        $LocalParseOk = [System.Net.IPAddress]::TryParse($LocalEndpoint.Trim('[', ']'), [ref]$LocalIp)
        $RemoteParseOk = [System.Net.IPAddress]::TryParse($RemoteEndpoint.Trim('[', ']'), [ref]$RemoteIp)
        $StateOk = $TcpState -in $ValidStates
        $PortOk = $LocalPort -le 65535 -and $RemotePort -le 65535
        $OwnerOk = $Owner -le [int]::MaxValue
        if (-not $PortOk -or -not $OwnerOk -or -not $StateOk -or -not $LocalParseOk -or -not $RemoteParseOk) {
            # Deliberately omit endpoint addresses and the original line.
            $SafeState = $TcpState.Substring(0, [Math]::Min(24, $TcpState.Length))
            throw "TCP inventory invalid: state=$SafeState stateValid=$StateOk pid=$Owner pidValid=$OwnerOk localPort=$LocalPort remotePort=$RemotePort portsValid=$PortOk localIpValid=$LocalParseOk remoteIpValid=$RemoteParseOk. All listeners were preserved."
        }
        $RecognizedOutput = $true
        if ($TcpState -eq 'LISTENING' -and $LocalPort -eq $Port) {
            $NetstatListeners += [pscustomobject]@{ LocalPort = [int]$LocalPort; OwningProcess = [int]$Owner }
        } elseif ($LocalPort -eq $Port -and $Owner -eq 0) {
            $ZeroOwnerNonListener = $true
        }
    }
    if (-not $RecognizedOutput) { throw 'TCP inventory returned no verifiable output. All listeners were preserved.' }
    if (@($CimListeners | Where-Object { $_.OwningProcess -eq 0 }).Count -gt 0) {
        # Shutdown can leave a stale CIM Listen/PID0 row. Ignore only when the
        # independently validated netstat table identifies PID0 as non-listening
        # on this port, and never if netstat itself reports a PID0 listener.
        if (-not $ZeroOwnerNonListener -or @($NetstatListeners | Where-Object { $_.OwningProcess -eq 0 }).Count -gt 0) {
            throw 'TCP inventory has an unverified zero-owner listener. All listeners were preserved.'
        }
        $CimListeners = @($CimListeners | Where-Object { $_.OwningProcess -ne 0 })
    }
    return ,@(@($CimListeners) + @($NetstatListeners) | Sort-Object LocalPort, OwningProcess -Unique)
}

function Get-DatabaseIdentity {
    $Hasher = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($Hasher.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($Database)))).Replace('-', '').ToLowerInvariant()
    } finally { $Hasher.Dispose() }
}

function Get-VerifiedRuntime {
    # A successful, identified service is stronger evidence than inventories that
    # Windows may silently omit. Never treat an HTTP response as a free port.
    $Runtime = $null; $Ready = $null; $HttpResponded = $false
    try { $Runtime = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/api/v1/demo/runtime" -TimeoutSec 3; $HttpResponded = $true }
    catch { if ($_.Exception.Response) { $HttpResponded = $true } }
    try { $Ready = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/readyz" -TimeoutSec 3; $HttpResponded = $true }
    catch { if ($_.Exception.Response) { $HttpResponded = $true } }
    $Listeners = Get-Listeners $ApiPort
    $Owners = @($Listeners | Select-Object -ExpandProperty OwningProcess -Unique)
    if ($Owners.Count -eq 0 -and -not $HttpResponded) { return $null }
    if ($Owners.Count -gt 1) { throw "Port $ApiPort has multiple listener owners; all were preserved." }
    if (-not $Runtime -or -not $Ready -or $Runtime.store_backend -ne 'sqlite' -or
        $Runtime.database_identity -ne (Get-DatabaseIdentity) -or $Ready.status -ne 'ready' -or
        -not $Runtime.process_id -or [long]$Runtime.process_id -le 0 -or [long]$Runtime.process_id -gt [int]::MaxValue) {
        throw "The service on $ApiPort could not prove the expected ready SQLite identity; it was preserved."
    }
    if ($Owners.Count -eq 0) {
        # Both inventories can be incomplete. Reuse only an already-recorded
        # launcher process, matching the live PID and expected database identity.
        try {
            if (-not (Test-Path -LiteralPath $StateFile -PathType Leaf)) { throw 'No trusted launcher state' }
            $Recorded = Get-Content -LiteralPath $StateFile -Raw | ConvertFrom-Json
            if ([long]$Recorded.api_process_id -ne [long]$Runtime.process_id -or
                $Recorded.database_identity -ne (Get-DatabaseIdentity)) { throw 'Launcher state mismatch' }
        } catch { throw "The healthy service on $ApiPort was omitted by inventory but has no matching trusted launcher state; it was preserved." }
    } elseif ([long]$Runtime.process_id -ne [long]$Owners[0]) {
        throw "The runtime PID does not match the listener on $ApiPort; all processes were preserved."
    }
    $ProcessInfo = Get-CimInstance Win32_Process -Filter "ProcessId=$($Runtime.process_id)"
    if (-not $ProcessInfo -or $ProcessInfo.CommandLine -notmatch '(?i)\buvicorn\s+services\.api\.app:app\b') {
        throw "Port $ApiPort belongs to an unrecognized process; it was preserved. Stop it through its original operator or choose the correct runtime manually."
    }
    return $Runtime
}

function Quote-FileArgument([string]$Value) {
    if ($Value.Contains('"')) { throw 'Unexpected quote in a file path.' }
    return '"' + $Value + '"'
}

if ($CheckOnly) {
    [pscustomobject]@{
        Mode = 'CheckOnly: no processes started, no files changed, no listeners stopped'
        Python = $PythonPath
        ApiPort = $ApiPort
        ApiListenerPresent = ((Get-Listeners $ApiPort).Count -gt 0)
        SQLiteFile = $Database
        DatabaseIdentity = Get-DatabaseIdentity
        PhoneApiUrl = "http://${LanAddress}:$ApiPort"
        ApkAvailable = (Test-Path -LiteralPath $Apk -PathType Leaf)
        DownloadRequested = [bool]$ServeApk
        DownloadPort = $DownloadPort
        DownloadListenerPresent = ((Get-Listeners $DownloadPort).Count -gt 0)
    }
    return
}

New-Item -ItemType Directory -Path $DataDirectory -Force | Out-Null
$Runtime = Get-VerifiedRuntime
if (-not $Runtime) {
    $Overrides = @{
        STREET_CEO_STORE = 'sqlite'
        STREET_CEO_SQLITE_PATH = $Database
        STREET_CEO_TRACE_DATABASE = $TraceDatabase
        STREET_CEO_REPOSITORY_ROOT = $Repository
        STREET_CEO_SEED_DEMO = '1'
        STREET_CEO_VOICE_ENABLED = '1'
    }
    $Previous = @{}
    try {
        foreach ($Name in $Overrides.Keys) {
            $Previous[$Name] = [Environment]::GetEnvironmentVariable($Name, 'Process')
            [Environment]::SetEnvironmentVariable($Name, $Overrides[$Name], 'Process')
        }
        $ApiProcess = Start-Process -FilePath $PythonPath -WorkingDirectory $Repository -WindowStyle Hidden -PassThru `
            -ArgumentList @('-m', 'uvicorn', 'services.api.app:app', '--host', '0.0.0.0', '--port', "$ApiPort", '--workers', '1') `
            -RedirectStandardOutput (Join-Path $DataDirectory 'demo-launcher-api.out.log') `
            -RedirectStandardError (Join-Path $DataDirectory 'demo-launcher-api.err.log')
    } finally {
        foreach ($Name in $Previous.Keys) { [Environment]::SetEnvironmentVariable($Name, $Previous[$Name], 'Process') }
    }
    $Deadline = [DateTime]::UtcNow.AddSeconds(20)
    do {
        Start-Sleep -Milliseconds 500
        $ApiProcess.Refresh()
        if ($ApiProcess.HasExited) { throw 'API exited during startup. Inspect data/demo-launcher-api.err.log locally; no listener was stopped.' }
        try { $Runtime = Get-VerifiedRuntime } catch { $Runtime = $null }
    } while (-not $Runtime -and [DateTime]::UtcNow -lt $Deadline)
    if (-not $Runtime) { throw 'API identity/readiness did not pass within 20 seconds. No process was stopped; inspect local launcher logs.' }
}

$State = @{ api_process_id = $Runtime.process_id; api_port = $ApiPort; database_identity = $Runtime.database_identity; updated_at_utc = [DateTime]::UtcNow.ToString('o') }
if ($ServeApk) {
    if (-not (Test-Path -LiteralPath $Apk -PathType Leaf)) { throw 'APK is absent. Build/package it before requesting -ServeApk.' }
    $ApkHash = (Get-FileHash -LiteralPath $Apk -Algorithm SHA256).Hash.ToLowerInvariant()
    $DownloadListeners = Get-Listeners $DownloadPort
    if ($DownloadListeners.Count -gt 0) {
        $DownloadOwners = @($DownloadListeners | Select-Object -ExpandProperty OwningProcess -Unique)
        if ($DownloadOwners.Count -ne 1) { throw "Port $DownloadPort has multiple listener owners; all were preserved." }
        $DownloadInfo = Get-CimInstance Win32_Process -Filter "ProcessId=$($DownloadOwners[0])"
        $HelperPath = Join-Path $PSScriptRoot 'serve_apk.py'
        if (-not $DownloadInfo -or $DownloadInfo.CommandLine -notmatch [regex]::Escape($HelperPath) -or
            $DownloadInfo.CommandLine -notmatch [regex]::Escape($Apk)) {
            throw "Port $DownloadPort belongs to an unknown download process; it was preserved."
        }
        try { $Download = Invoke-RestMethod -Uri "http://127.0.0.1:$DownloadPort/artifact.json" -TimeoutSec 3 }
        catch { throw "Port $DownloadPort belongs to an unverified download service; it was preserved." }
        if ($Download.service -ne 'street-ceo-apk-only' -or $Download.sha256 -ne $ApkHash) {
            throw "Port $DownloadPort is not serving this APK; its listener was preserved."
        }
    } else {
        $DownloadProcess = Start-Process -FilePath $PythonPath -WorkingDirectory $Repository -WindowStyle Hidden -PassThru `
            -ArgumentList @((Quote-FileArgument (Join-Path $PSScriptRoot 'serve_apk.py')), '--apk', (Quote-FileArgument $Apk), '--host', '0.0.0.0', '--port', "$DownloadPort") `
            -RedirectStandardOutput (Join-Path $DataDirectory 'demo-launcher-download.out.log') `
            -RedirectStandardError (Join-Path $DataDirectory 'demo-launcher-download.err.log')
        $Deadline = [DateTime]::UtcNow.AddSeconds(10)
        do {
            Start-Sleep -Milliseconds 400
            $DownloadProcess.Refresh()
            if ($DownloadProcess.HasExited) { throw 'APK download service exited. No other listener was stopped.' }
            try { $Download = Invoke-RestMethod -Uri "http://127.0.0.1:$DownloadPort/artifact.json" -TimeoutSec 2 } catch { $Download = $null }
        } while (-not $Download -and [DateTime]::UtcNow -lt $Deadline)
        if (-not $Download -or $Download.sha256 -ne $ApkHash) { throw 'APK download service could not verify its artifact within 10 seconds.' }
    }
    $State.apk_sha256 = $ApkHash
    Write-Output "APK download: http://${LanAddress}:$DownloadPort/street-ceo.apk"
    Write-Output "APK SHA-256: $ApkHash"
}
$State | ConvertTo-Json | Set-Content -LiteralPath $StateFile -Encoding UTF8
Write-Output "API ready: http://${LanAddress}:$ApiPort"
Write-Output 'Phone: connect to the same network and set this URL in Profile > Shop connection.'
Write-Output 'Existing catalogue and sales were retained. No firewall rules or unknown processes were changed.'
if ($LanAddress -eq '127.0.0.1') { Write-Output 'For a phone, rerun with -LanAddress followed by this computer''s reachable LAN IPv4 address.' }
