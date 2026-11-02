# Connected phone demo checks

Use the exact APK hash reported by the launcher. Keep the phone and API computer
on the same reachable network. This checklist records actual observations; a
build or unit-test pass is not a phone result.

## Start or inspect the demo

From repository root in PowerShell:

```powershell
.\infra\start-demo.ps1 -CheckOnly -LanAddress 192.168.10.213 -ServeApk
.\infra\start-demo.ps1 -LanAddress 192.168.10.213 -ServeApk
```

Replace the address with the computer's reachable LAN IPv4 address. CheckOnly
does not start processes or change files. The launcher uses API port 8001 and
`data/demo-mvp.sqlite3`, preserving existing records. It reuses only a verified
ready SQLite runtime with the expected database identity and PID. Unknown
listeners are left running. The optional port 8081 service exposes only
`/street-ceo.apk` and artifact metadata, never a directory listing or repository
files. No firewall rule is created. If the phone cannot connect, inspect network
reachability with the operator; do not assume a working localhost check proves LAN
access.

Download `http://<computer-address>:8081/street-ceo.apk` on Android, install it,
and enter `http://<computer-address>:8001` in Profile > Shop connection. If 8001
is an older unverified listener, the launcher refuses to replace it; the operator
must use that process's original control to stop/restart it. Port 8000 is untouched.

## Record these observations

| Check | Expected observation | Actual / evidence |
|---|---|---|
| Installation | Correct APK opens, expected shop connection and catalogue load | Pending |
| First microphone grant | Android asks once; granting leads to listening in foreground Sell | Pending |
| Wake and framing | Say “Apo one Coke Napo”; visible reviewed basket contains one Coke | Pending |
| Tender and change | Say “Cash five” when asked; server receipt shows catalogue total, 5.00 received and exact change | Pending |
| Next sale | After spoken success, wake listening resumes; a second complete command works without re-enabling | Pending |
| Unknown product | “Apo one unicorn Napo” speaks/displays clarification; no receipt or stock change | Pending |
| Partial invalid basket | Valid product plus unknown product rejects whole basket | Pending |
| Cash shortfall | Insufficient cash asks for a corrected amount; no receipt or stock change until adequate | Pending |
| Bank | Bank receipt has exact total and zero change; settlement is not claimed | Pending |
| Manual cash | Review manual basket, enter received cash, record receipt with exact change; stock/history agree | Pending |
| Cancel | Cancel tender collection; old basket is not silently sold by the next wake command | Pending |
| Background return | Switch apps during idle/tender/output, return; no stale prompt/sale or stuck microphone | Pending |
| Denied permission | Clear explanation and manual sale remain usable; re-grant through Android settings works | Pending |
| Request investigation | Shop request list is readable, correlates voice review/receipt and distinguishes parser/provider | Pending |
| API restart | Operator restarts known SQLite runtime; catalogue, stock, history and exact retry remain preserved | Pending |
| Connection failure | No fake success; uncertain sale recovery retains original key rather than creating another sale | Pending |

Use synthetic demo products/data. Record APK SHA-256, API identity, Android
version/device, time, exact phrase and actual outcome. Preserve failure details
without credentials or personal data. Do not mark pending rows passed without
observing them on a physical device.
