# Runako — Lessons

No lessons recorded yet. Initialized 2026-10-29; no work performed.

## 2026-10-31 — W3/W4 verified findings

- A source-defined route can still return 404 on an older running listener.
  Frontend tests/source inspection are not proof that that listener was updated.
- The seeded shop ending 0001 is non-nil. Reject true nil/malformed IDs before
  request construction; do not invent replacement defaults from an error alone.
- Relative activity age and current assignment are different facts. Preserve
  exact timestamps and disclose repository-mtime provenance.
- Product image API returns metadata without byte retrieval; a local blob preview
  must not be represented as a durable backend URL.
- Requested browser viewport override was ineffective (1280 innerWidth remained).
  Desktop checks passed; phone verification is not claimed.

### 2026-10-31 — W5 demo/costs/mobile findings

- Same host port through LAN and localhost exposed different effective APIs
  (13vs32routes). Confirm actual OpenAPI/shop response before blaming UUID/UI.
- Viewport tool targets selected tab; always measure actual innerWidth and
  client/scroll widths. A430request measured431; do not claim exact430.
- Native date automation may need real keyboard input/blur to commit React
  state; DOM value alone did not prove state. Actual expense later saved exactdate.
- Invoice confirmation adds stock; missing direct correction contract is a
  material product gap, not grounds to invent a route or dummy receipt.

### 2026-10-31 — W6 polling dashboard

Successful frequent polls can coexist with stale repository evidence. Display
server-generation, browser-receipt, source-activity and observed-change times
separately. Tests/commits/files have different attribution/time precision; do
not manufacture execution timestamps or inflate old handoff pass mentions.

### 2026-10-31 — W5 costs finalization

Current backend added direct cost corrections after earlier frontend blocker;
verify source AND running OpenAPI before declaring a missing contract. Legacy
catalogue GET is /shops/{id}/products while new costs are /api/v1/shops/...;
versioning cannot be inferred. DOM settled receipt and native audit verify
confirmation; a transient Confirming state is insufficient. Browser chooser
timeout did not bound runtime; avoid long event waits when other verification
can proceed. Crypto Uint8Array must use ArrayBuffer generic for current DOM
TypeScript types; focused HTTP-LAN fallback tests plus build verify this helper.

## 2026-10-31 — W6-VOICE-ERROR-001
Transport error wording must reflect endpoint side effects. Transcript/audio failure cannot imply a sale mutation; reserve unknown-sale recovery for commit/undo. Endpoint reachability on PC does not establish phone connectivity.

## 2026-10-31 — W6-VOICE-PROFILE-001
APK origin http://localhost differs from Vite http://localhost:5173. CORS must whitelist exact actual shell origin; health GET from PC alone misses JSON POST preflight failure. All Python text edits use explicit UTF-8 for TSX Unicode arrows/symbols.

## 2026-11-01 — SPRINT90-UX-002
An uncertain mutation must remain uncertain if recovery later returns4xx; only verified receipt/reversal settles it. Parent flow lock must derive from pending+uncertain+tender state; unconditional finally-onBusy(false) can unlock manual checkout or navigation and lose recovery context. Receipt success and subsequent history/summary refresh failures are separate outcomes. Payment word parsing must preserve framed raw amount words rather than use catalogue quantity normalization.

## 2026-11-01 — PHONE-RECOVERY-001
No-storefetch alone cannot defeat a worker that manuallyreturns cachedAPIJSON or HTMLfallback. Use network-only API/no-store/crossorigin routing plus cachebustedprobes duringworkerupgrade. BrowsernetworkOnline onlysignal is not shopreachability. Incompletepaymentquestion request cannotpostsale by currentcontract; classify independently from actualpaidmutation while preserving priorunknown. Never replace originalpaidpayload with missingamountfallback duringuncertainrecovery.

## 2026-11-02 — STARTER-COGS-UX-001
InstalledTypeScript7.0.2 rootmodule exportsversionmetadata, notlegacycreateSourceFile/ScriptTarget API. Fixtureparitytests can readboundedstaticliteral withoutimportingbrowsernetworkmodule andcomparecanonicalJSON; avoidnewtestdependency onunstablecompilerAPI.

## 2026-11-02 PRODUCT-DIAGRAM-001
BrowsercanloadSVGyetPlaywrightscreenshot hangsafterfontsloaded. Bound browserwork and use directvectorPDF+Popplerrender for staticartifact. ReportLab hexcolorstrings require expandingthree-digit#fff to#ffffff to preserveSVGwhite; inspectactualfinalPNG beforeclaimingvisualpass. MobileHTMLchecks remainseparate fromvectorrender.

## 2026-11-02 QUANTITY-REPLY-UX-001
ASRfinished latchcanremainstuckifhandlerpromisediscardedandeffectdepsunchanged. Re-armafterhandlercompletiononlyifcurrentforegroundandnotdisposed. Stoppingnativeclearsownershipbeforependinghandlerends: keepstoppedcurrentlooplifecyclefeedbackbutresultsstrictowner; documenthidden guardsinclude lateReady, notonlyStart. Fake-native lifecycletestsneededbeyondparserfixtures. MissingAPIreplytracealonecannotproveexactdevicecause.
