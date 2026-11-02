# Runako — Memory

Initialized 2026-10-29. No prior sessions; no work performed yet.

## Project facts (confirmed)

- Street CEO hackathon MVP; deadline November 4, 2026.
- Web UI: React + TypeScript PWA, mobile-first, accessible dashboards.
- No application code exists yet; `apps/web/` not yet scaffolded.

## Stable context

- Role: `agents/runako/role.md`. Activation protocol: `AGENTS.md` section 2.
- Owns UI components/pages/styles; Fambai owns the offline layer inside the app.
- Consumes Hwaro's API contracts; never invents endpoints.

### 2026-10-31 — Confirmed cost workflow constraints

Product costs support six decimal places(integer micros); expenses are integer
cents. Cost correction replaces recorded unit cost without stock receipt;
invoice/purchase confirmation receives stock with weighted-average cost. Seven
expense categories: electricity,transport,rent,wages,airtime,supplies,other.
Recurring entry records supplied period and does not schedule future charges.
Runtime invoice upload currently returns provider_unavailable/no extracted
lines; manual source review only. See latest W5 handoff for time-bounded evidence.
