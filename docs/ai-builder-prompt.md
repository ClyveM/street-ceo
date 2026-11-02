# Copy-ready AI builder prompt

Build **Street CEO — Your shop, in control**, a polished mobile-first tuckshop
sales demo. Read `docs/product-demo-builder.md` as the authoritative requirements
and `docs/product-diagram/index.html` for the flow.

Deliver catalogue → manual or hands-free Apo sale → stock → sales history, with
a connected FastAPI/SQLite backend and Android packaging where supported. Use the
existing logo, friendly navy/green/teal, small warm gold accents, clear type,
large touch targets and compact screens. Exclude the separate team-view app.

Make Sell the hero. Support the entire conversation without per-stage taps:
“Apo, one Coke and two sugar, Napo” → product confirmation when needed →
“Cash ten dollars” → saved total6.30/change3.70 → next Apo closes the completed
receipt and starts another sale. Yes/No/Cancel, quantity and payment replies do
not need another wake phrase. Keep typing available. Native Android must request
permission, pause recognition during its own speech, resume afterwards and respect
explicit Pause. Do not promise background wake listening.

Show items, Total, Tendered and large Change on the receipt. Put diagnostics,
transcripts, references and stock-only Undo caveats under Details & help. Keep
errors and uncertain paid outcomes visible. Reserve Android system/keyboard
insets; use transient upward-swipe reveal for system navigation.

Use `services/api/demo_catalogue.json` for all six products, prices, quantities
and illustrative unit costs. Never invent supplier costs or historical COGS.
Prices, totals, stock and change are server authoritative. Exact retry returns
the same durable receipt; failed transactions leave no partial changes.

Keep exact catalogue matches quick. Safe local proposals require spoken Yes and
honest local provenance. Harder phrases can call actual Muse with a short bounded
wait. Reject unknown IDs, invented quantities and partial baskets. Never silently
remove a possible product word. Missing data gets a question. Bank is recorded
tender, not verified settlement. Persist sanitized correlated requests/responses;
keep provider keys in the backend and secrets, traces and databases out of Git.

Add basic mobile reports: monthly summary and product sales for inclusive dates
or Today/20/90-day presets in the shop timezone. Keep old product amounts unknown
where historical line prices are missing. Add a spoken “end my day” flow from
idle Sell: counted cash → opening if unknown → server expected/count/difference
→ explicit confirmation. Cash sales contribute sale total, not tendered amount;
include recorded cash movements. Bank remains uncounted here. Preserve zero vs
unknown, stale-preview checks, original retry keys and immutable saved closes.
Month-end review offers optional Count stock or Skip, with no forced count or
claim of a ledger period lock.

Provide runnable source, setup instructions and tests. Demonstrate manual and two
consecutive voice sales, correct stock/history, restart durability, unknown-product
handling, underpayment and duplicate-request protection. If only a prototype is
possible, label mocked capabilities and missing native/backend work explicitly.
