# Repository cleanup QA — 2026-11-02

REPO-CLEAN-QA-001 checkpoint: local source/bootstrap gates PASS; staged-export installation/build/testing pending coordinator.

## Ownership and audit

Full activation restored. QA writes tests/infra/.github/own brain only. Root owns ignores, README/environment example, staging and commit/push; Runako owns shop/local-office separation, Hwaro optional API team extraction. No file deletion, live data/provider/runtime operations or host escalation by QA. No credentials or attachment contents inspected.

Ignore audit sent root: logs at any depth, remote-chat attachments, .pytest-* fixtures, tsbuildinfo, data, generated Android bundles/build/cache/local.properties/keystores. Keep package locks, Android Gradle wrapper JAR/properties/scripts, native source/config/resources, six-product catalogue, shop test fixtures and intentional logos. The only discovered unignored binaries over1MB were the two deliberate1.45MB logo assets. Nested Android ignores already exclude copiedCapacitor assets/config/plugin metadata and generatedCordova files; recreate with normal sync. Root updated .gitignore; root must remove previously tracked generated/private/team files from index while preserving local copies.

## Added or changed QA files

- infra/dev.py: cross-platform check/setup/api/web. Setup creates/reuses .venv, pip requirements and npmci. API foregroundlocalhost8001/oneworker, absoluteprojectSQLite/trace defaults, demo seed/voice on and localteamoff; web points to localhost8001/defaultshopUUID. Explicit environment values preserved; no secret copying or killing processes. Prerequisite check discovers versions, not exhaustive compatibility validation. Android setup remains separate.
- infra/check_source_manifest.py: staged filenames only; checks required locks/wrapper/catalogue/logo/envexample/setup and refuses generated/private/optionalteam paths. Never opens private payloads. Requires its own currentGitindex.
- tests/test_dev_bootstrap.py and tests/test_source_manifest.py: guard fresh defaults/override preservation and artifact/source boundaries.
- tests/test_security.py: scan Gittracked plus nonignored source, avoiding ignored attachments/config/generated output; trackedignored source still scanned. Regression verifies this. Existing tracked/nonignored env gate unchanged.
- .github/workflows/quality.yml: Pythonmemory/seed0 isolation, source manifest gate and all independent backend acceptance; Node22 lockednpmci, shoptests/build and independentclient checks. CI configured, not observed remote green.
- tests/README.md: exact setup/gate contracts and isolatedGitindex requirement.

## Executed evidence

- python infra/dev.py check: Python3.13.6, Node22.18.0, npm10.9.3 discovered, pass.
- Focused security/bootstrap/manifest9 passed1.48s.
- python tests/run_checks.py with memory/seed0:29 passed20.129s, bytecode compilation passed.
- After adding optionalAPIteam path rejection, focusedbootstrap/manifest4 passed0.15s.
- Scoped git diff --check passed; only existing Windows newline conversion notices.
- Prestage manifest correctly reported trackedtsbuildinfo and missingnewsource dependencies. This is expected before rootstage; no final source-export pass claimed.

## Required final gate

Root stages intendedsource preserving localignoredfiles, then runs source manifest. Export only that index to a new directory and install/build/test without local-office/teammodules/node_modules/.env/databases. Security tests must use the export's ownGitindex, never accidentally find a parentindex. Run npmci frontendtests/build, piprequirements and isolatedbackend+baseline suites. Root handles network/host permissions. No clean-clone/easy-setup completion claim until these results arrive. APK/phone acceptance unaffected and separate.

## Final staged-export gate — PASS

Coordinator reports361 staged source paths; source manifest passed in both repository index and isolated data/source-export-20261102 with its own Git index. Previously tracked generated/team paths were removed from the index only; local copies preserved. Fresh exported Python venv/pip requirements and npmci completed successfully without ignored local dependencies.

Root-attributed final exported results:

- Complete backend/independent pytest255 passed12.50s, no warnings with LLAMA settings empty.
- Baseline29 passed10.630s.
- Frontend117 passed802ms; production build65modules/indexonly, no office bundle.
- Isolated freshSQLite uvicorn on a free port became ready, returned six costed products, exposed no office/team routes; root terminated only its test process afterwards. An initial403 from missing X-Shop-ID was fixed in the probe; the application guard behaved correctly.
- Two stale retail test fixtures were repaired by their owner, and root corrected temporary-directory setup; final run green. These are final results, not a claim earlier attempts all passed.
- Root reports SVG/PDF/PNG diagram visual review and HTML390/320-width no-overflow checks passed. QA read README, environment example, builder brief/prompt and boundaries: setup commands match actual bootstrap, canonicalcosts and source/provider/device limits remain honest.

Final source/clean-checkout software gate **PASS**, no remaining concrete blocker in this scope. Global cached whitespace check noted existing trailing-space/EOF notices in several legacy/newly staged paths; no functional or secret finding and no product edits made for cosmetic cleanup before commit. Remote GitHub Actions has not been observed green. Root owns commit/push and any resulting CI outcome; installed APK/runtime/physical-phone acceptance remain separate. No ignored data deleted, source staged, live runtime changed or provider called by QA. All QA files and own handoff persisted; no active QA processes.
