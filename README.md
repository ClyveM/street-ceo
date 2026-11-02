# Street CEO

**Your shop, in control.** A connected Android sales assistant for a small
Zimbabwean tuckshop: catalogue → manual or hands-free Apo sale → stock → sales
history. FastAPI stores shop data in local SQLite. Meta/Muse helps with harder
product interpretation; exact matches and safe local proposals work without a key.

Mobile **Reports** provides monthly and product sales with date filters. From
idle Sell, say **“end my day”** for a confirmed counted-cash comparison. Month-end
review includes optional stock count or Skip. See
[reports and closing](docs/reports-and-close-acceptance.md).

## Run it on your computer

Install **Python 3.11+** (3.13 tested), **Node.js 22.18+ with npm**, and Git.
Internet access is needed for the first dependency installation.

```sh
git clone https://github.com/ClyveM/street-ceo.git
cd street-ceo
python infra/dev.py check
python infra/dev.py setup
```

Then use two terminals in the repository root:

```sh
# Terminal 1 — persistent demo API
python infra/dev.py api
```

```sh
# Terminal 2 — web app
python infra/dev.py web
```

Open **http://127.0.0.1:5173**. API readiness is at
**http://127.0.0.1:8001/readyz**. On systems that use `python3`, substitute it
for the initial `python` commands. The helper creates `.venv`, installs Python
requirements and uses the committed npm lockfile. Servers run in the foreground;
Ctrl+C stops them. Startup preserves existing databases and configuration.

The six starter products include illustrative prices, stock and unit costs for
future COGS. State persists in `data/demo-mvp.sqlite3`; request/response traces
are separate. Both stay local and ignored. See [starter costs](docs/starter-demo-costs.md).

A fresh checkout automatically seeds these six products when the API first starts.
Normal startup preserves existing shop data; it does not reset sales. An explicit
`STREET_CEO_SEED_DEMO=0` disables seeding. Allow roughly **5–15 minutes** for browser
setup with the prerequisites already installed and working internet; this is an
estimate and depends on download speed. Android builds require additional setup.

## Enable cloud Muse

Copy `.env.example` to a local `.env`, then set `LLAMA_API_KEY` and `LLAMA_MODEL`
to values enabled for your Meta account. Restart the API. Keys stay on the
backend; never put them in `VITE_` variables. Without a key, manual sales and
exact/local catalogue paths remain usable; cloud-only checks report unavailable.

The API development terminal shows local versus Muse handling, timing and
sanitized request/response details. See [terminal activity logging](docs/terminal-muse-logging.md)
for output modes and watching the background demo server.

Native Android speech uses the phone's recognition and text-to-speech. A browser
needs microphone permission and supported speech APIs; remote HTTP microphone
access may be restricted. Typing remains available. The full hands-free demo
requires Android installation and physical-device testing.

## Build an Android demo

Install Android Studio, its Java runtime and Android SDK 35. The Android project
and Gradle wrapper are included; generated APKs are not committed. Use your PC's
reachable LAN address in the web build and run the API on `0.0.0.0`.

Follow [Android setup](apps/android/README.md) and the [demo runbook](docs/demo-runbook.md).
Browser setup does not require Android Studio. The demo is connected; offline
sync and PostgreSQL deployment are deferred. Building is not phone acceptance.

## Product and builder handoff

- [Product documentation and acceptance](docs/product-demo-builder.md)
- [Copy-ready AI builder prompt](docs/ai-builder-prompt.md)
- [Product diagram](docs/product-diagram/index.html)
- [Verified implementation and device-test limits](docs/demo-mvp-verification.md)

## Repository boundaries

`apps/web` is the shop UI; `apps/android` is its native wrapper. Backend and
domain code lives under `services`; `tests` and `infra` contain checks and launch
tools. `agents`, `tasks` and `AGENTS.md` retain development records.

The separate Project Operations Office/team-view application is **local-only**,
ignored and optional. Default shop startup, builds and tests do not require it.
It is not included in a clone or the shop build. Historical notes may mention it.
See [repository boundaries](docs/repository-boundaries.md).

## Verify changes

Activate `.venv`, then run:

```sh
python -m pytest services tests/sqlite_demo_acceptance.py
python tests/run_checks.py
```

Or use `.venv/bin/python` on macOS/Linux or `.venv\Scripts\python.exe` on Windows.
For the frontend:

```sh
cd apps/web
npm run test:frontend
npm run build
```

GitHub Actions runs committed shop checks. Public deployment, authentication
hardening and full accounting certification are separate work.
