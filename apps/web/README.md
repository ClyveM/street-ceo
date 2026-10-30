# Street CEO web app

The first mobile-first PWA slice lives here. It includes the Today, Sell, and
Stock surfaces, a manual sale basket, cash/bank tender selection, responsive
layout, and explicit loading/empty/error/demo/offline states.

## Local development

From `apps/web/` run:

```text
npm install
npm run dev
```

For a dependency-free visual review, open `apps/web/design-preview.html`
directly in a browser (double-click it or use the browser's Open File action).
It is a static design preview and does not replace the React app or require npm.
Use its bottom navigation to review Today, Sell, Stock, and the 2D Team Monitor;
the Team view links to the simulated 3D Command Room and back.

Open the printed local URL (normally `http://localhost:5173`). To use a local
API instead of the labeled starter catalogue, set `VITE_API_BASE_URL` before
starting Vite. The client uses the documented `GET /shops/{shop_id}/products`
and `POST /shops/{shop_id}/sales` contract, including `X-Shop-ID` and an
`Idempotency-Key` for sale writes.

The fourth bottom-nav item, `Team`, opens the local Team Monitor. It shows the
six project lanes, task and changed-file snapshots from a local activity model,
and a simulated typing-style preview. The preview is explicitly labeled as a
simulation and is not a live subagent stream.

From that view, choose `Open 3D room →` for the CSS/HTML command room. It
includes the CTO desk, one desk and planner card per specialist lane, and a
shared wall board with task, commit, unit-test, and warning stats. Choose
`Back to 2D monitor` at any time to use the original 2D view as a fallback.

The preview uses the deterministic local dataset in `src/App.tsx`. A host that
has real local activity can inject a `window.__STREET_CEO_TEAM_ACTIVITY__`
snapshot before the app loads; the UI uses that snapshot when present and falls
back to the deterministic dataset otherwise. Neither source exposes private
agent thoughts or a line-by-line generation stream.

The service worker, IndexedDB, and sync queue are intentionally not included;
those belong to Fambai's offline layer.
