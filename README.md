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

The six starter products include illustrative prices, stock, unit costs for
future COGS, and bundled product illustrations: cola, bread, sugar, milk, chips
and soap. These images ship with the repository and need no image downloads or
Muse key. State persists in `data/demo-mvp.sqlite3`; request/response traces
are separate. Both stay local and ignored. See [starter costs](docs/starter-demo-costs.md).

A fresh checkout automatically seeds these six products when the API first starts.
Normal startup preserves existing shop data; it does not reset sales. Starter
images fill missing images only for the matching demo products; uploaded product
images are preserved. An explicit
`STREET_CEO_SEED_DEMO=0` disables seeding. Allow roughly **5–15 minutes** for browser
setup with the prerequisites already installed and working internet; this is an
estimate and depends on download speed. Android builds require additional setup.

## Enable cloud Muse

Copy `.env.example` to a local `.env`, then set `LLAMA_API_KEY` and `LLAMA_MODEL`
to values enabled for your Meta account. Restart the API. Keys stay on the
backend; never put them in `VITE_` variables. Without a key, manual sales and
exact/local catalogue paths remain usable; cloud-only checks report unavailable.

Handwritten daily-sheet reading additionally requires an image-capable
`LLAMA_VISION_MODEL` enabled for your account. Uploads produce editable proposals;
review actual quantities, selling amounts and cash/bank totals before confirming.
The demo accepts only today's open business day and unrecorded sales whose stock
has not already been deducted or covered by a later count. Daily sheets are
aggregates, not invented customer receipts; unsupported historical costs remain
unknown. See [capture and sharing acceptance](docs/capture-sharing-acceptance.md).

Under Reports, CSV exports contain text data; the companion PDF contains the
Street CEO logo. The updated APK opens Android's share chooser. A browser can
download CSV or open the print dialog to save the branded PDF. Exports preserve
the selected period, currency and incomplete-data labels. Product images saved
to the shop can load on the sale screen after restart.

The API development terminal shows local versus Muse handling, timing and
sanitized request/response details. See [terminal activity logging](docs/terminal-muse-logging.md)
for output modes and watching the background demo server.

Native Android speech uses the phone's recognition and text-to-speech. A browser
needs microphone permission and supported speech APIs; remote HTTP microphone
access may be restricted. Typing remains available. The full hands-free demo
requires Android installation and physical-device testing.

## Download the Android demo

[Download the Street CEO Android APK](https://raw.githubusercontent.com/ClyveM/street-ceo/main/releases/street-ceo-demo-2026-11-04.apk)
from this repository. This is a debug-signed demo build. Install it on Android
and grant microphone permission to use hands-free sales.

SHA-256: `836a5f5a967aead172b627c24b651b8b394db1e8f2c95ec86892b9d093e1ce8f`.

The APK needs a running Street CEO API. On the computer hosting the API, follow
the setup steps above, then start it from the repository root on a reachable
interface using the activated Python environment:

```sh
python -m uvicorn services.api.app:app --host 0.0.0.0 --port 8001 --workers 1
```

Connect the phone and computer to the same network. In the app's **Profile →
Shop connection**, enter your computer's LAN address, for example
`http://192.168.1.20:8001`, and keep the default demo shop ID. Check that the
phone can reach the server on port 8001. The API uses `data/demo-mvp.sqlite3` by
default. To enable cloud Muse, configure the backend as described above.

## Build an Android demo

Install Android Studio, its Java runtime and Android SDK 35. The Android project
and Gradle wrapper are included. Use your PC's
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
