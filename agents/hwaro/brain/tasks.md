# Hwaro — Tasks

## Assigned by Mutungamiri

### W1-HWARO-001 — Backend foundation and transaction contracts — complete 2026-10-30

- Scope: `services/api/` only, plus backend-owned updates to `docs/api-contracts.md` when needed.
- Read `AGENTS.md`, this role, all six brain files, `docs/architecture.md`, `docs/api-contracts.md`, `docs/product-requirements.md`, and `tasks/master-board.md` before coding.
- Build a minimal FastAPI foundation with health/readiness, shop/product/sale domain schemas, deterministic validation, and an idempotent sale boundary suitable for UI, offline, and voice callers.
- Do not implement frontend, offline, voice, AI, finance, or inventory-owned code. Coordinate contract assumptions through the shared API contract file and handoff.
- Acceptance: runnable app/test entry point; tenant/shop scope represented; sale retry returns the original result for the same key and rejects a changed payload; no silent negative stock; tests recorded in handoff.
- Before completion update only this agent's relevant brain files and write a structured handoff. No fabricated test results.

Evidence: `services/api/app.py`, `services/api/test_app.py`,
`services/api/requirements.txt`, and `docs/api-contracts.md`; six tests passed
and compileall completed successfully on 2026-10-30. HTTP transport limitation
is recorded in `current-state.md` and `lessons.md`.

No tasks assigned yet. Initialized 2026-10-29.

## W3-MUSE-SHOP-001 — complete 2026-10-31

- Verified the frontend's stable shop ID against the backend seed.
- Made local memory demo seeding explicit in `Settings` and default-on only for
  memory mode; PostgreSQL remains synthetic-data free.
- Evidence: Muse/seed/persistence focused tests passed; full API suite passed.

## W3-TEAM-CHAT-API-001 — complete 2026-10-31

- Added `POST /api/v1/team/chat/messages` and
  `GET /api/v1/team/chat/{agent}/messages`.
- Evidence: focused chat history test passed; full API suite 27 passed.
- Contract and reset behavior documented in `docs/api-contracts.md`.

## W3-LIVE-DESK-STATUS-API-001 — complete 2026-10-31

- Added exact timestamp sources and freshness fields to the team activity API.
- Defined evidence semantics for Runako: filesystem mtime for agent brain files;
  Git committer timestamp for the latest commit.
- Evidence: focused team activity tests and full API suite passed.

## W4-PROJECT-OFFICE-API-001 — complete 2026-10-31

- Added reusable office endpoints under `/api/v1/office/` for projects,
  rooms, product/workstream records, assignments, status evidence, and room
  chat.
- Added cross-room validation, in-memory reset semantics, and safe bounded
  metadata contracts.
- Evidence: `test_project_office.py` 3 passed; full API suite 31 passed.

## W4-MUSE-SHOP-ID-001 — complete 2026-10-31

- Confirmed deterministic shop ID and local seed behavior.
- Live smoke: health 200, products 200, Muse POST 200 with `needs_data` and no
  fabricated profit.
- Browser reset action: clear localStorage key `street-ceo-api-config` or save
  the backend base URL with shop ID `00000000-0000-0000-0000-000000000001`.

## W4-PRODUCT-IMAGE-API-001 — complete 2026-10-31

- Added shop-scoped product-image upload/access metadata and social image
  generation contract.
- Evidence: focused social/image tests 5 passed; full API suite 37 passed.
- Durable storage is unavailable in this MVP; metadata and bytes reset on API
  restart and generation explicitly returns provider unavailable.

## W4-SOCIAL-DATA-001 — complete 2026-10-31

- Added the shop-scoped Social Update selection contract and image metadata
  validation under `/api/v1/shops/{shop_id}/social/brief`.
- Added tests for exact repository product values, unknown-product rejection,
  MIME/size validation, and no fabricated inventory.
- Evidence: focused social tests 3 passed; full API suite 34 passed.

### W3-VOICE-INPUT-001C — Voice transport endpoint — assigned 2026-10-30

- Define a backend-local voice transcript/audio request boundary for the web
  microphone flow. Keep credentials server-side and return bounded status/error
  shapes only.
- Integrate the existing Meta Llama interpreter without allowing model output to
  post a sale directly. Preserve shop scope and idempotency.
- Scope: `services/api/` only, with API contract updates and tests.

Task assignments from Mutungamiri will appear here under an
"Assigned by Mutungamiri" section.

### W4-SOCIAL-IMAGE-API-FINAL-001 / W5-DEMO-READINESS-API-001 — completed 2026-10-31

- Backend-only finalization and four-day demo happy-path audit.
- Added/verified draft-only social text and image-generation routes, generation
  retrieval, product-image input wiring, shop scope validation, and explicit
  provider-blocker responses.
- Live evidence: restarted listener passed health, seeded catalogue, sale and
  stock summary, Muse, product image upload, social routes, team chat, and
  project-office smoke checks.
- Remaining blockers: no `MUSE_IMAGE_MODEL` is configured; image bytes and
  generation records are in-memory and reset on restart; the image adapter
  contract still needs Ungwaru to verify provider model propagation before a
  credentialed image call is claimed.

### W2-HWARO-001 — PostgreSQL persistence adapter — active 2026-10-30

- Scope: `services/api/` and backend-owned persistence documentation only.
- Read the latest W1 handoff, `docs/api-contracts.md`, and Ruzivo's accounting memo before changing persistence.
- Replace the in-memory-only limitation with a clear PostgreSQL-ready repository boundary, environment configuration, schema/migration starting point, and tests. Preserve API behavior and idempotency. Keep local development runnable without credentials through an explicit test store or local mode.
- Do not implement finance, inventory, UI, offline, or voice-owned code.
- Acceptance: persistence boundary explicit, no secrets committed, tests cover replay and shop scope, and handoff states what still requires a live PostgreSQL service.

### W3-LIVE-TEAM-001A — Local team activity API — active 2026-10-30

- Scope: `services/api/` only.
- Add a local-development-only `GET /api/v1/team/activity` route that derives a safe activity snapshot from the configured repository root: master-board task statuses, recent Git commit count, changed-file summaries, agent current-state/handoff timestamps, and available test evidence. Keep the route read-only and never expose secrets, file contents, private prompts, or arbitrary filesystem paths.
- Make the repository root configurable and test with a temporary fixture; return a clear unavailable/error state when the local root is absent. Preserve production behavior when the monitor is disabled.
- Acceptance: response schema is documented, tests cover parsing and unavailable state, and the frontend can poll it without authentication in local mode only.

#### Evidence checkpoint — 2026-10-30

- Added `services/api/persistence.py`, `services/api/migrations/0001_initial.sql`,
  and `services/api/test_persistence.py`.
- Updated `services/api/app.py`, `services/api/requirements.txt`, and
  `docs/api-contracts.md` within backend ownership.
- `python -m pytest services/api -q` — **9 passed**.
- `python -m compileall -q services/api` — **exit 0**.
- No secrets committed. Live PostgreSQL execution remains outstanding.

### W3-LIVE-TEAM-001A evidence — 2026-10-30

- Added `services/api/team_activity.py` and `services/api/test_team_activity.py`.
- Updated `services/api/app.py`, `services/api/persistence.py`, and
  `docs/api-contracts.md` within scope.
- `python -m pytest services/api -q --basetemp .pytest-basetemp` — **12 passed**.
- `python -m compileall -q services/api` — **exit 0**.
- Fixture tests cover board parsing, timestamps/test evidence, safe content
  omission, missing-root unavailable state, and disabled production behavior.

### W3-VOICE-INPUT-001C evidence — 2026-10-30

- Added `services/api/voice_boundary.py`, `services/api/VOICE_API_CONTRACT.md`,
  and `services/api/test_voice_boundary.py`.
- Updated `services/api/app.py` and `services/api/persistence.py` only within
  backend ownership.
- `python -m pytest services/api -q --basetemp .pytest-basetemp` — **18 passed**.
- `python -m compileall -q services/api` — **exit 0**.
- Tests cover bounded transcript intent, confirmation, no sale mutation,
  transcript replay/conflict, audio validation/unavailable response, audio
  replay/conflict, and disabled behavior.

### PostgreSQL runtime priority slice evidence — 2026-10-30

- Expanded `services/api/persistence.py` with transactional PostgreSQL shop,
  product, and sale operations; updated `services/api/app.py` to delegate all
  existing mutating/read routes through the repository boundary.
- Added `services/api/PERSISTENCE_RUNTIME.md` and no-service readiness tests in
  `services/api/test_persistence.py`.
- `python -m pytest services/api -q --basetemp .pytest-basetemp` — **20 passed**.
- `python -m compileall -q services/api` — **exit 0**.
- No PostgreSQL credentials or live service were present; no live migration
  claim is made.
# W3-TEAM-MESSAGE-API-001 — completed

- Scope: verify and contract-test `POST /api/v1/team/messages`.
- Evidence: focused test 5 passed; full API suite 24 passed; compileall passed.
- Finding: route exists in the current checkout. The live 404 came from a stale
  backend process; after restart the POST smoke test returned 201.

### W5-COSTS-INVOICES-API-001 — completed 2026-10-31

- Added backend-only invoice upload/review/confirm, product unit-cost and
  stock update audit, guided expense draft/confirm, and profitability inputs.
- Upload/extraction never fabricates OCR. Missing OCR is returned explicitly;
  review lines require shop-scoped matching and confirmation before mutation.
- Remaining limitation: PostgreSQL schema starting points are present, but
  PostgresRepository CRUD for invoices, costs, audits, expenses, and sale COGS
  is still a follow-up before PostgreSQL runtime can be called complete.

### W5-FINAL-COST-001 — completed 2026-10-31

- Added separate product-cost correction draft/confirm contract with strict
  Decimal/micros validation, effective date, reason, source reference, actor,
  and direct-correction audit semantics.
- Confirmation changes cost basis only; it never adds stock or alters stock
  quantity. Verified with focused tests and a restarted-listener smoke test.
- Accounting review is routed to Verengai/Ruzivo in `docs/api-contracts.md` and
  the Hwaro handoff; PostgreSQL CRUD remains the durable-runtime follow-up.

### W5-FILM-READY-API-001 — completed 2026-10-31

- Replaced the stale LAN API process with the current backend bound to
  `0.0.0.0:8000`; verified the phone address exposes 35 OpenAPI paths versus
  the stale listener's 13.
- Added safe local demo reset/seed and authoritative `stock_after` sale
  response data so the summary can update without a reload.
- Verified the full LAN happy path. PostgreSQL durability and image-provider
  configuration remain separate blockers, not silently claimed as complete.
### W6-REALTIME-OPS-MVP-API — completed 2026-10-31

- Scope: fastest safe demo polling contract using the existing team activity
  endpoint; backend only.
- Result: `GET /api/v1/team/activity` now exposes server generation time,
  latest verified repository evidence time/source, freshness, age, and safe
  current repository event payloads.
- Evidence: focused tests 8 passed; full suite 79 passed; LAN smoke passed
  after restarting the stale listener.
- Explicit non-goal: no live agent heartbeat, live typing, or inferred active
  work was implemented in this 30-minute cut.
### W5-VOICE-TEXT-API-001 — completed 2026-10-31

- Fixed the typed multi-item transcript boundary and safe provider-error
  mapping in the backend. Added catalogue-scoped `lines` and `error_code`.
- Verified aliases against the seeded demo shop: Coke → Coca-Cola 300ml and
  Sugar → Sugar 1kg.
- Evidence: focused 10 tests, full suite 85 tests, and LAN smoke after
  restarting the current Uvicorn listener.

### W6-RETAIL-CONTROL-API-001 — implementation checkpoint — 2026-10-31

- Implemented backend contracts/routes for purchase drafts/confirmation,
  stock-take drafts/confirmation, and end-of-day close.
- Added focused tests for new/existing products, weighted-average cost,
  confirmation gates, stock adjustments, tender requirements, and variances.
- Full suite passed 95 tests. Finance review is required for purchase/close
  ledger mapping before durable PostgreSQL integration.
### W6-RETAIL-ATOMIC-001 — completed 2026-10-31

- Resolved partial purchase mutation and retry duplication by staging all
  lines and persisting the original confirmation result.
- Added invoice-reference dedupe, stocktake baseline conflict/recovery, and
  explicit sales-only day-close preview semantics.
- Evidence: focused 5 passed; full suite 101 passed; live LAN regression
  smoke passed.

### W6-DAY-CLOSE-001 — completed 2026-10-31

- Full recorded-movement preview and idempotent confirmed posting verified by
  6 focused tests and LAN smoke.
- Remaining dependency: PostgreSQL transaction/ledger persistence and finance
  review before production release.
### W6-VERIFY-DATA-001 — completed with social blockers — 2026-10-31

- Controlled demo data and read-back verification completed on the LAN
  listener; exact IDs/effects are recorded in `handoffs.md`.
- Muse profitability and retail read paths passed. Social brief passed;
  social draft schema mismatch and image-generation timeout remain for
  Ungwaru/provider coordination.

### W6-DEMO-BACKEND-001 — completed verification — 2026-10-31

- Verified healthy current LAN runtime (48 OpenAPI paths), purchase atomicity, product-cost correction, voice commit, and day-close post/replay/readback.
- Fresh suite: 69 passed; separate synthetic-shop live smoke passed. Seeded demo not reset. Added reusable backend smoke script.
- PostgreSQL durability, ledger integration, finance review and provider verification remain separate dependencies. See handoffs.md for evidence.

### W6-DEMO-BACKEND-001 — proven blocker fixed — 2026-10-31

- Reproduced duplicate sale/stock decrement from one voice review with a new key on LAN; fixed review-to-sale binding and stable original receipt replay.
- Fresh suite 74 passed; patched LAN full regression passed after listener restart. Restart clears prior temporary QA data. See handoffs.md for exact IDs, scope and limitations.

### W6-PERSISTENCE-COGS-001 — completed 2026-10-31

- Scope: `services/api/persistence.py` and focused persistence coverage.
- Fixed PostgreSQL sale COGS write/read mapping and product cost reload.
- Evidence: persistence tests 7 passed; app/voice/retail regression 26 passed
  with 8 existing SSL deprecation warnings; compileall and scoped diff-check
  passed. Live PostgreSQL execution remains outstanding.

### W6-APK-VOICE-CORS-001 — source fix/tests complete; runtime activation pending —2026-10-31
See handoff. No restart authorized/performed.

## Assigned by Mutungamiri — 2026-11-01 — SQLITE-ASSESS-001
Read-only SQLite feasibility assessment requested by Owner. Load AGENTS.md, role.md, six brain files, shared architecture/API docs and master board. Inspect services/api persistence and mutation paths. Assess exact durable demo scope, PostgreSQL coupling, minimum safe SQLite approach, restart/idempotency/atomicity, effort and blockers. No product changes. Permitted writes: own brain only, structured handoff. Do not run live mutations/restarts or inspect secrets. Return concrete recommendation and 90-minute priorities.

SQLITE-ASSESS-001 completed 2026-11-01: read-only feasibility and effort assessment persisted in handoffs.md/current-state.md; no implementation or new test evidence.

## Assigned by Mutungamiri — 2026-11-01 — DEMO-SQLITE-VOICE-001
Implement durable SQLite online single-worker demo in services/api/ only plus own brain. Load full activation protocol. Own all API integration including persistent sanitized request/response trace records (coordinate AI trace schema), voice reviews/commit/retry, manual sale/catalogue/stock/history persistence. Use explicit versioned encoding and atomic staged request unit-of-work if suitable; never pickle. Preserve existing work and API contracts. Test real DB reopen, replay/conflict, rollback, seed preservation and voice commit tender/change durability. User requires APK hands-free Apo sale with unknown products rejected and correct change. No offline additions. Do not restart live services without coordinating root; no secrets in output. Own API tests. Coordinate interfaces promptly with Runako and Ungwaru. Persist handoff.

DEMO-SQLITE-VOICE-001 complete2026-11-01: source stable; parent host181passed including independentQA; structured handoff persisted. Live launch/phone/finance review remain parent-owned.

## Assigned by Mutungamiri — 2026-11-01 — SPRINT90-API-002
90-minute improvement sprint authorized Owner. Full AGENTS activation. Own services/api + own brain only. Improve exact MVP: add optional manual cash received to SaleCreate/create route and server authoritative change using integer cents, preserve legacy omission compatibility and voice contracts/retry fingerprint. Add shop-scoped bounded sanitized recent voice/Muse trace read endpoint for investigation (filter shop and optional correlation, never return other-shop/global traces or credentials). Publish exact contracts promptly to Runako. Add real-file/manual amount/retry/conflict/crossshop trace tests. No unrelated finance/offline/invoice changes or live restart. Root runs host ASGI tests; do not wait subagent escalation. Checkpoint after15min or milestone. Persist handoff.

SPRINT90-API-002 source complete2026-11-01;10SQLite tests authored, compile/diffPASS; parent host validation pending. See structured handoff; no live restart.

## Assigned by Mutungamiri — 2026-11-01 — PHONE-RECOVERY-API-001
FullAGENTS activation, ownAPI+brain only; investigate actualphone screenshot uncertain beforepayment. Root read-onlytraces currentUTC19:50 vs latesttrace18:51; prior4commitresponses200needs_tender withvalidquestion, no newtrace at19:47/48 screenshots. Inspect persisted defaultreview381f947c-c95f-45d8-88ec-8553b2fbf491 and confirmedsale bindings read-only; do not dumpPII/transcriptsbrain orpostanything. Determine whether actualsale exists for review, noreset/replaylivecommit. Add regression actualHTTP no-tender->cash-noamount->cashpaid chain + repeatquestion/no stockmutations; preserve originalreviewkeys. Check CORS/responseheaders200JSON canread viaAPK. Need concretefacts, no speculativefix unless repro. No escalations/liverestart; root handles checks. Persist handoff.

## Assigned by Mutungamiri — 2026-11-01 — CATALOGUE-VOICE-API-001
FullAGENTS activation. Owner reports recentApo/Napo fails andMuse not reasoningovercatalogue. Root verifiedearlyreturn rejectsparsefailure wheneverproducts exist, soMuse nevercalled. Logs sanitizedactual examples 1 bread glove number;1 coca-cola nabo marble;bath soap nabo maple map;coca-cola noquantity. OwnAPI+brain only. Implement catalogue-aware resolution integration via Ungwaru services.ai resolver: exactdeterministicpath staysfast; uncertain/nonexactfallback calls configuredMuse withactualcatalogue, knownIDs/prices/stock validated, no inventedproducts orquantityguess. Nonexact proposals REQUIREexplicituser matchconfirmation beforecommit (newrequestbool orreviewconfirmationendpoint coordinatefrontend); ambiguous/missingquantity asksclarification, mixedunknown neverpartialposts. Preserve voice paididempotencyfingerprints/reviews acrossschemaextensions, SQLitepersistence, tracingactualprovider_called no falsecataloguelabel. Add realHTTP regressions ambiguous/proposedconfirm/no mutation thenpayment/retry, modelunavailable usefulfallback. Coordinate contracts immediately Runako/Ungwaru. No liveposts/restart/secrets/escalations; root hosttests. Persist handoff.

CATALOGUE-VOICE-API-001 source ready2026-11-01; four HTTP regressions authored, own compile/diffPASS; root hostvalidation pending. Full structured handoff persisted. No live restart/sale.

## Assigned by Mutungamiri — 2026-11-02 STARTER-COGS-001
Ensure starter/demo catalogue has explicit illustrative unit costs for COGS. Own services/api/ and own brain only. Load full activation protocol and latest demo docs/board. Inspect both memory and SQLite seed behavior; add safe default costs for new starter products and a narrowly scoped missing-cost backfill for existing exact demo starter SKUs without overriding known costs, prices, stock or historical sale snapshots. Coordinate Ruzivo illustrative cost values/accounting. No live DB mutations or restart: root integrates. Write focused meaningful tests in owned services/api/test*.py, persist handoff. Do not touch frontend; report parity needs.

STARTER-COGS-001 source ready2026-11-02: threefocusedtests authored, compile/diffPASS; root hosttests and Ruzivoactualcodereview pending. Frontendparity reportedPASS. No liveDB/start/restart.

STARTER-COGS-001 focusedvalidation2026-11-02: PASS12 own starter+cost suites after meaningfulresetfixture update;8existingSSLwarnings. Sourcecomplete, no liveactivation; rootbroadQA/finance review remain.


## Assigned by Mutungamiri — 2026-11-02 REPO-SHOP-API-001
Fullactivation services/api ownbrain scope. Userwantsseparatedteamviewapp excludedfromrepo/build. Audit app.py unconditionalteam/projectofficeimports+routes; refactor optionalmount module so ignoredteamimplementation canremainlocalbutcleanclonestarts StreetCEO withoutteamcode. Rootowns.gitignore; sendexactteamonlypathsmanifest. Keep agentsbrain/projectdocumentation tracked. Teamfeatureslocaloptional explicitlyenabled, defaultStreetCEOnooffice/team endpoints. PreserveSQLite/Muse/voice/pricing/costs. ExistingAPItests team-only may moveignoredlocalmodule/testfolder; no deletinglocalfiles. Providebootstraprequirementsfreshcloneconfig, includetzdataifWindowsneeds. NoDBmutation/restart/escalation; focusedtests/handoff.

REPO-SHOP-API-001 complete2026-11-02: optionalteam extracted/preserved, defaultshop startswithoutteamdependencies; focused26PASS/compile/diffPASS. Rootownsignore/index/publication. No liveDB/restart.


## Assigned by Mutungamiri — 2026-11-02 QUANTITY-REPLY-API-001
Fullactivation APIscopeownbrain. Verify scopedbare'one'/'1' response currentmissingqtyreview (exactchips vsASRputadochipsnaples), preserveproductcontext withoutrequiringApo/repeatwholebasket. roottraceoriginal15:30UTC nofollowup request sofrontendlikelyblocking; auditbackendexistingclarification prependsoldnoisytranscript leading tosecondMusewait evenrecognizedsingleproduct. Fixonlyconfirmed scopedcontextgap withsafeexplicitqty/allitems/noinvention/confirmation; tests tempDB. No liveoriginalreviewcommit/replay/restart/escalation. Handoff.

QUANTITY-REPLY-API-001 explicitnarrowAIextension: services/ai/catalogue_voice.py clarificationtargetdataclass/qualifyingmissingqtyreturns only +relatedAItests ifneeded. No matchingthreshold/deadline/providerchanges. Structuredtarget onlysafeuniquesingleitem/providervalidated match; no groundingfromquestionstring or blindlyplausiblepartialunknown. QAindependentguard.

QUANTITY-REPLY-API-001 complete2026-11-02: owncompile/diffPASS, parenthostfullservices+independent310PASS38.75s includingnew20. Structuredhandoffpersisted, no liveoriginalreview/restart. Rootcoordinatesactivation/phoneacceptance.


## Assigned by Mutungamiri — 2026-11-02 REPORTS-CLOSE-API-001
Fullactivation APIscope ownbrain. Ownerrequests mobilemonthlysalessummary/productsales betweeninclusiveuserdates+last1/20/90days; voiceEndmyday askscashonhand reconcilesopening+sales/movements difference,monthendstockcountoptional. Auditexistingdaycloseopening bug (sumsallopeningbeforeday; no same-daybaseline), coordinateRuzivo authoritativepolicy BEFOREchangingfinancialrules. Implement shopscoped read-onlyreports API boundedperiodslocaltimezone, currentnamevsreceipthistorytruth, missingCOGSexplicit, sales/tender/reversal semantics perreview. Extendcash-onlydailyclose safely separatebankunknown(nofakezero), explicitopeningrecord/source+count+confirmation,idempotency/restart/frozenrecovery, previewversionstalecheckifnecessary. Reuseexistingretail endpoints/contracts withoutbreakinglegacyUI. SendexactAPIcontractRunako early. No liveDBchanges/restart/escalation. TesttempDB+handoff.

REPORTS-CLOSE-API-001 source frozen2026-11-02: exactcontractdoc, ownpure13PASS4.78s/compile/diffPASS; parentfullintegration+Ruzivoactualcodereview pending. No liveDB/restart.

REPORTS-CLOSE-API-001 final financial blocker repaired2026-11-02: explicitopening generic bypass closed afterlegacyreplay; future actualcash guarded+previewexcluded; own15focusedPASS3.97s, parentaffectedtests/finalfinancialsignoffpending. Source frozen.

## Assigned by Mutungamiri — 2026-11-02 TERMINAL-MUSE-001
Implement Owner-approved readable backend terminal logging: heard transcript, local vs provider routing, actual sanitized provider request/response in demo detail mode, durations, validated basket product names/qty and clarification/failure honesty. Modes off/normal/detail via STREET_CEO_CONSOLE_TRACE; development launcher defaults detail for requested demo, direct API normal default. No secrets/raw ANSI/control injection; bounded safe printable output, correlated concurrent requests, no sale behavior change. Temporary explicit scope extension: services/ai/tracing.py, new services/ai/console_trace.py, services/api trace middleware/app hooks as necessary, infra/dev.py defaults, .env.example and focused tests. Single writer all listed paths. Load AGENTS, own role/six brains, relevant docs and master board. Persist handoff/tests. Do not restart live API or call paid provider. Root owns docs.

TERMINAL-MUSE-001 source frozen 2026-11-02: focused31 PASS5.89s; root QA/activation pending; no live mutation.

## Assigned by Mutungamiri — 2026-11-02 MUSE-SALES-ANSWERS-001
Owner mostsellingproduct AskMuse invalidunavailable; endpoint onlytotal/count evidence missingproductranking. Scope services/api/app.py,new insight helper if needed,focusedAPItests; nofinancecodechanges. Followactivationprotocol6brains/docs/board. Implement deterministicrepository answers for clear best/mostselling/topproduct questions (defaultexplicitthismonth; byquantityunlessrevenueexplicit; ties,nosales,missingoldlabels honest), and simple todays/monthsales total. Reuse reports.py authoritative snapshot/dateTZ/uniquehistorical semantics; additive responseperiod/coverage only if frontend parserallows, otherwise evidenceids+answerdates sufficient. Clearly source repository notmodel; existingprofitpath unchanged; non-simple questionskeepMuse. No hallucination unsupportedquery as generic totals; tests. No live mutation/restart/cloud. Persisthandoff. AIpromptfixUngwaruparallel files separate.

MUSE-SALES-ANSWERS-001 source frozen 2026-11-02:17focusedPASS2.19s; independentQA/rootactivation pending.
