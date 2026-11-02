# Starter COGS QA — 2026-11-02

Task STARTER-COGS-QA-001. Targeted software gate: **PASS**.

Scope: product read-only; tests/infra and own brain writes. Restored AGENTS, role, six brain files, current task/board, demo acceptance and Ruzivo's review-STARTER-COGS-REVIEW-001. Reviewed canonical JSON, backend seed/cost audit/startup transaction, and frontend fallback/parity test.

- Exact default shop UUID/name/currency/timezone and product UUID/shop/SKU/name are required. Changed or deleted products are preserved, not recreated.
- Missing means None only. Known zero/custom costs, invoice provenance and prior audit history prevent overwrite. Selling prices and stock remain unchanged.
- Demo audits identify illustrative STARTER-COGS-001 assumptions, not supplier evidence: no invoice, no receipt quantity, no stock movement.
- Startup fault injected after SQL writes rolls back both costs and audits; reopened database remains identical to legacy state, subsequent clean startup succeeds.
- Historical unknown/zero COGS and receipt fingerprints remain unchanged. Future sales snapshot current cost; exact retry returns the saved receipt without another stock decrement, including after reopen and later cost changes.

Executed with STREET_CEO_STORE=memory and STREET_CEO_SEED_DEMO=0 before Python imports:

- `python -m pytest tests/starter_cogs_acceptance.py services/api/test_starter_costs.py -q -p no:cacheprovider --basetemp .pytest-chengetai-starter`: **13 passed in 1.24s** (10 independent, 3 owner).
- From apps/web, `node --experimental-strip-types --test tests/starterCatalogue.test.mjs`: **1 passed**, 158.4022ms. All six IDs, prices, stock and illustrative costs match canonical source.

Files added: tests/starter_cogs_acceptance.py and this report; own brain appended. No product edits, HTTP/provider calls, live sales, reset, runtime restart, host escalation or Android packaging. Temporary database tests establish software behavior, not a live migration claim. Ruzivo approved these illustrative assumptions and controls; this does not establish historical acquisition costs, net profit, tax or full accounting completion.

Next: coordinator completes integrated suite and reserved APK/runtime verification. Preserve old unknown COGS; never retrospectively fill it. Any scope change affecting costs or accounting returns to Ruzivo and QA.
