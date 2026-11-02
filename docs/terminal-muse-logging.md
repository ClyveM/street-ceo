# Terminal Muse activity

The backend terminal shows command processing. Vite's `hmr update` messages
only describe frontend source refreshes.

`STREET_CEO_CONSOLE_TRACE` selects the output:

- `normal`: command input, local/provider provenance, result and timing.
- `detail`: also includes bounded sanitized provider request/response payloads.
- `off`: suppresses this terminal activity output; persistent investigations remain.

The development helper defaults to `detail`:

```powershell
python infra/dev.py api
```

Set a mode before starting the backend to override the helper:

```powershell
$env:STREET_CEO_CONSOLE_TRACE = 'normal'
python infra/dev.py api
```

Restart an already running backend to load code or environment changes. Do not
start a second backend against the same SQLite file. Web and APK requests both
reach the same backend; no APK rebuild is required for server logging.

For the Windows launcher that runs the backend in the background, watch its
redirected output from a terminal in the repository root:

```powershell
Get-Content .\data\demo-launcher-api.out.log -Tail 40 -Wait
```

Ctrl+C stops watching the file; it does not stop the background API.

Use request correlation IDs to follow interleaved commands. Provider timing and
total API timing are different: total API timing includes routing and database
work, but not the phone's speech recognition or spoken reply. A provider response
is a proposal, not proof that a sale was saved. A late provider response after a
timeout must not be presented as an accepted basket. Local commands explicitly
identify that Muse was not called. Unknown and ambiguous inputs remain visible.

For the Owner-approved longer-wait demo, catalogue interpretation can wait up to
24 seconds for Muse (catalogue HTTP budget 25 seconds; voice client 30 seconds).
The terminal shows the actual provider and API durations. Waiting longer gives
a slow response time to arrive; it does not guarantee a catalogue match.

Payloads reuse the investigation sanitizer: credentials, binary data and basic
personal information are redacted, output is bounded and terminal control
characters must not execute. The display shows what speech recognition supplied;
it cannot recover the original spoken audio or prove recognition accuracy.
Existing sanitized persistent investigations remain in the separate local trace
database, excluded from Git.
