# W6-DEMO-QA-001 — Release-gate evidence

Chengetai · 2026-10-31 · Verdict: BLOCK release; local functional checks pass.

## Fresh commands and results

- `python tests/run_checks.py`: FAIL. Six tests executed: four pass, one failure, one error. Backend smoke import raises `ModuleNotFoundError: services` because the documented script invocation does not put repository root on its import path. Environment-file check rejects `.env` and `apps/web/.env.local`. Both are ignored and untracked (`git ls-files` empty; `git check-ignore` lists both); this is not evidence of committed credentials. Secret-pattern scan passed. Environment contents were not inspected.
- `python -m pytest services -q --basetemp .pytest-chengetai-w6-001`: FAIL collection: bare imports `boundary` in AI tests and `state_machine` in voice tests cannot resolve.
- PowerShell `$env:PYTHONPATH='.;services/ai;services/voice'; python -m pytest services -q --basetemp .pytest-chengetai-w6-002`: PASS, 131 passed, 8 SSL deprecation warnings, 31.59 seconds. Explicit path workaround does not repair default invocation.
- `npm run test:frontend` in `apps/web`: PASS, 89/89, zero skips.
- `npm run build` in `apps/web`: PASS, 73 modules, shop and office entries.
- `git diff --check`: PASS, exit 0; line-ending warnings only.

## LAN smoke

Command: `python infra/w6_demo_qa.py`. HTTP-only local requests needed approved network access after restricted sockets returned WinError 10013. No TLS verification was disabled. A first urllib attempt also encountered the host SSL keylog permission configuration; direct HTTP avoided creating an unnecessary TLS context.

Target: `http://192.168.10.213:8000`. Health and readiness return 200; OpenAPI returns 200 with 48 paths.

All writes used a new synthetic shop `4a7c4270-4308-4036-b4a3-6b06904f1dd1`; no demo reset or prepared-shop write. Synthetic records remain in the server until its normal cleanup/restart.

| Gate | Result | Exact evidence |
|---|---|---|
| Purchase/WAC | PASS | Two unpaid purchases: 10 units at 1,000,000 micros and 10 at 2,000,000; stock 20, cost 1,500,000 micros |
| Sale/stock/retry | PASS | Sale `fddf17bf-cd3f-4480-8955-31f7c13dab43`: 2 units, 400 cents, stock 18; exact retry same response; changed tender with same key 409; stock remains 18 |
| Day-close | PASS (memory-mode functional) | Full recorded movements; Africa/Harare; expected/counted cash 400 cents, bank/card 0; both variances 0; audit `eccddba6-ce76-4ca3-8bc2-982d57e38bc6`; exact retry same response |
| Muse | PASS repository calculation | `answered`, source `repository`: sales USD 4.00, COGS USD 3.00, expenses USD 0.00, profit USD 1.00; evidence IDs for all four inputs |
| Social brief | PASS | `catalogue_source: repository` |
| Social text | PASS response contract | `status: draft`, `source: provider`, `provider: meta_muse_text`, no warnings |
| Social image | PASS response contract; visual review BLOCKED | `status: draft`, `provider: meta_muse_image`; unpublished draft warning. No image bytes/appearance/download inspected; no publication performed |

## APK artifact

`apps/android/android/app/build/outputs/apk/debug/app-debug.apk`: 7,167,699 bytes.
SHA-256: `4f4e0762a980cb495e94869212e740b5d1611d6b89688edeca2b0987ed0be77c`.
Python zipfile integrity check: no bad member; AndroidManifest.xml and dex present.
Compared every file in freshly built `apps/web/dist` against `assets/public/` inside APK: zero mismatches.
Artifact packaging PASS. Physical device install, signature verification, permissions, microphone, camera/gallery, network from phone, and export/download are BLOCKED/unverified; no connected-device test was performed.

## Release blockers and re-entry

1. Baseline runner must resolve root imports; the unchanged documented command must pass.
2. Environment-file policy currently fails on ignored runtime configuration. Reconcile local/CI policy without deleting user configuration, weakening committed-secret controls, or exposing values; rerun baseline.
3. Default combined service command needs import-safe tests or a documented supported test environment; rerun exact command.
4. Required authentication gate is unmet: source shop dependency compares caller-supplied X-Shop-ID with path ID; that is scoping, not authenticated identity. No production security approval is issued. Local debug cleartext is documented; production transport requires HTTPS.
5. CI green and physical-phone end-to-end evidence are not established in this session. Image visual/download QA and offline/reconnect demonstration remain unverified.
6. Purchase, close, invoice and related operational records remain documented in-memory. No database durability, migration, concurrent transaction or restart-survival release approval is issued. Financially significant changes still require Ruzivo review.

No product features or other agents' files were changed. Added only this evidence report, QA smoke script, and Chengetai memory entries. Web build regenerated its normal build outputs.
