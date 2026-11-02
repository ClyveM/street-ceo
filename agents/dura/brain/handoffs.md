# Dura — Handoffs

## Handoff — W2-DURA-001 — 2026-10-30

### Assignment

Implement inventory receipt, sale, return, adjustment, and stock-count movement
primitives with pack conversion, quantity-weighted average cost, source
references, and safe negative-stock handling. Scope was `services/inventory/`
only.

### Files changed

- `services/inventory/__init__.py` — public exports.
- `services/inventory/movements.py` — `InventoryBook`, movement/value models,
  pack conversion, WAC, audit validation, and negative-stock protection.
- `services/inventory/test_movements.py` — five focused behavior tests.

### Verified tests

- `python -m pytest services/inventory/test_movements.py -q` — 5 passed.
- `python -m compileall -q services/inventory` — passed.
- `python -m pytest -q` — not green because collection fails in unrelated
  `services/ai/test_boundary.py` and `services/voice/test_state_machine.py`
  (`ModuleNotFoundError` for same-directory imports).

### Integration notes and outstanding issues

- `InventoryBook` is intentionally in-memory and transaction-neutral; Hwaro must
  persist stock and movement append atomically.
- Sales have negative `Movement.quantity`; receipts and resalable returns are
  positive. A sale movement records pre-sale WAC as `unit_cost` and COGS as
  `total_cost`.
- Resalable returns require `original_unit_cost`; non-resalable returns are
  rejected until represented by a separate stock-loss adjustment.
- No API, finance, UI, offline, or voice files were changed.

## 2026-10-31 — W6-DEMO-INVENTORY-001
- Validated current central purchase, invoice and stocktake implementation; no API/frontend changes.
- Fresh check: `python -m pytest services/inventory/test_movements.py services/api/test_retail_control.py services/api/test_costs.py -q`: 18 passed in 7.85s.
- Tests cover existing/new product WAC, purchase prevalidation and replay, review-first invoice receipts, stocktake baseline conflicts and audits.
- Extra probe confirmed duplicate existing-product purchase lines are rejected by PurchaseCreate.
- BLOCKER: legacy invoice confirmation mutates each line before validating later lines. Probe: reviewed two-line invoice, invalidate second matched product, confirm twice. Starting stock 2 became 3 then 4; audits 1 then 2; invoice stayed needs_review. Failed retries duplicate the first receipt. Evidence: services/api/app.py confirm_invoice loop. Hwaro must stage/validate all lines and commit atomically; serialize concurrent confirmations. No backend edits made due to ownership.
- Limitations: endpoint/in-memory tests, no PostgreSQL/concurrency or frontend verification. WAC integer micros truncation remains distinct from Decimal inventory precision; missing historical cost must remain disclosed.
- Next: Hwaro fix invoice atomicity and add regression; Chengetai verify concurrency/persistence before release.

## 2026-10-31 — W6-DEMO-INVENTORY-001 follow-up
- Rechecked purchase, stocktake, invoice and manual cost correction tests: pre-change 18 passed in 5.82s.
- Scoped fix: InventoryBook.adjust now rejects bool, fractional Decimal/float, and string quantities before mutation; previously adjustment accepted fractional units contrary to whole-base-unit policy. Added five regression cases preserving stock and movement history.
- Files changed: services/inventory/movements.py, services/inventory/test_movements.py, own brain checkpoint files.
- Invoice atomicity blocker remains visible in current confirm_invoice implementation; API ownership stays Hwaro. No API/frontend changes. Central purchase stages updates and guards replay; direct correction tests verify quantity unchanged and repeat confirmation rejected; stocktake tests verify review and stale-baseline conflict.
- Next: Hwaro repair invoice partial mutation/retry; Chengetai validate persistence/concurrency. No production readiness claim.
- Post-fix focused verification: python -m pytest services/inventory/test_movements.py services/api/test_retail_control.py services/api/test_costs.py -q — 23 passed in 15.40s.

## 2026-10-31 — W6 inventory replay follow-up

### Assignment

Fix one proven remaining inventory issue within `services/inventory/`, covering
purchase capture and replay safety without changing API, finance, UI, offline,
or voice ownership.

### Files changed

- `services/inventory/movements.py` — track the first movement for each
  `(source_reference, product_id)` pair; return it for an exact replay and
  reject changed movement data before stock mutation.
- `services/inventory/test_movements.py` — regression coverage for exact
  purchase replay, conflicting retry rejection, and multi-product invoice
  sources.

### Verified tests

- `python -m pytest services/inventory/test_movements.py -q` — 12 passed.
- `python -m compileall -q services/inventory` — passed.
- `python -m pytest services/inventory/test_movements.py services/api/test_retail_control.py services/api/test_costs.py -q` — 25 passed in 9.81s.

### Outstanding issues and handoff instructions

- The previously reproduced API invoice confirmation defect remains: a later
  invalid line can leave earlier lines received, and a retry can duplicate
  stock. It is in `services/api/app.py`, outside this assignment's permitted
  ownership. Hwaro must stage/validate all invoice lines and commit atomically,
  with concurrent confirmation protection.
- API integer-micros WAC rounding and persistence/finance journal integration
  also remain separate integration blockers. No production-readiness claim is
  made.
