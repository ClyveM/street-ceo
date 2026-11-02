"""Counted-cash reconciliation, explicit balance anchors and frozen receipts."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from services.api.retail_control import CashClosePreview


def cash_events(record):
    zone = ZoneInfo(record.shop.timezone)
    events = []
    for sale in {sale.id: sale for _, sale in record.idempotent_sales.values()}.values():
        if sale.tender == "cash":
            events.append({"id": str(sale.id), "date": sale.created_at.astimezone(zone).date(), "at": sale.created_at, "posted": sale.created_at, "amount": sale.total_cents, "kind": "sales"})
    from .paper_sales import confirmed_batches
    for batch in confirmed_batches(record):
        events.append({'id':str(batch.id),'date':batch.business_date,'at':batch.confirmed_at,'posted':batch.confirmed_at,'amount':batch.cash_cents,'kind':'sales'})
    for expense in record.expenses.values():
        if expense.status == "confirmed" and expense.tender == "cash":
            events.append({"id": str(expense.id), "date": expense.occurred_on, "at": datetime.combine(expense.occurred_on, datetime.min.time(), zone), "posted": expense.confirmed_at or expense.created_at, "amount": -expense.amount_cents, "kind": "expenses"})
    for purchase in record.purchases.values():
        if purchase.status == "confirmed" and purchase.tender == "cash":
            amount = -(purchase.total_cost_micros // 10000) if purchase.total_cost_micros % 10000 == 0 else None
            events.append({"id": str(purchase.id), "date": purchase.purchase_date, "at": datetime.combine(purchase.purchase_date, datetime.min.time(), zone), "posted": purchase.confirmed_at or purchase.created_at, "amount": amount, "kind": "purchases"})
    for movement in record.cash_movements.values():
        if movement.tender == "cash" and movement.kind != "opening_balance":
            events.append({"id": str(movement.id), "date": movement.occurred_at.astimezone(zone).date(), "at": movement.occurred_at, "posted": movement.created_at, "amount": -movement.amount_cents if movement.kind == "refund" else movement.amount_cents, "kind": "refunds" if movement.kind == "refund" else "adjustments"})
    return events


def calculate_cash_preview(record, business_date):
    zone = ZoneInfo(record.shop.timezone)
    start = datetime.combine(business_date, datetime.min.time(), zone)
    end = start + timedelta(days=1)
    now = datetime.now(timezone.utc)
    dated_events = [event for event in cash_events(record) if event["date"] <= business_date]
    events = [event for event in dated_events if event["at"] <= now]
    openings = [item for item in record.cash_movements.values() if item.kind == "opening_balance" and item.tender == "cash" and item.occurred_at <= start]
    candidates = [(item.occurred_at, item.created_at, "explicit_opening", item) for item in openings]
    for close in [*record.day_closes.values(), *record.cash_closes.values()]:
        if close.business_date < business_date:
            candidates.append((datetime.combine(close.business_date + timedelta(days=1), datetime.min.time(), zone), close.confirmed_at, "prior_counted_close", close))
    warnings = ["Bank/card has not been counted or reconciled; no settlement verification is implied."]
    if len(events) != len(dated_events):
        warnings.append("Future-effective cash activity is excluded until it has actually occurred.")
    opening = None
    source = "missing"
    source_id = None
    carry = []
    if candidates:
        anchor_at, _, source, anchor = max(candidates, key=lambda item: (item[0], item[1]))
        source_id = anchor.id
        opening = anchor.amount_cents if source == "explicit_opening" else anchor.cash_counted_cents
        if source == "explicit_opening":
            carry = [event for event in events if event["date"] < business_date and event["at"] >= anchor_at]
        else:
            previous_ids = set(getattr(anchor, "source_ids", []))
            if not previous_ids:
                warnings.append("Prior legacy close lacks complete source IDs/cutoff evidence; possible late/backdated ordering remains uncertain.")
            carry = [event for event in events if event["date"] < business_date and (event["date"] > anchor.business_date or (event["id"] not in previous_ids if previous_ids else event["posted"] > anchor.confirmed_at))]
            if anchor.cash_variance_cents:
                warnings.append("Prior counted close had an unresolved variance; its counted cash is carried forward.")
            if any(event["date"] <= anchor.business_date for event in carry):
                warnings.append("Late/backdated cash activity after the prior frozen close is included in the carried opening; the prior receipt is unchanged.")
        if any(event["amount"] is None for event in carry):
            opening = None
        else:
            opening += sum(event["amount"] for event in carry)
    else:
        warnings.append("Opening cash is unknown. Explicitly record the start-of-business opening, including acknowledged zero, before closing.")
    today = [event for event in events if event["date"] == business_date]
    buckets = {kind: 0 for kind in ("sales", "expenses", "purchases", "refunds", "adjustments")}
    payment_review = any(event["amount"] is None for event in [*carry, *today])
    for event in today:
        if event["amount"] is not None:
            buckets[event["kind"]] += event["amount"]
    if payment_review:
        warnings.append("A cash purchase has fractional-minor-unit valuation without a saved actual payment; payment review is required, not silent rounding.")
    if any(item.created_at.astimezone(zone).date() == business_date for item in record.voice_sale_reversals.values()):
        warnings.append("Stock-only reversals do not establish cash refunds; cash sales remain recorded until an explicit refund movement exists.")
    source_ids = sorted({event["id"] for event in events} | {str(item.id) for item in openings} | ({str(source_id)} if source_id else set()))
    data = {"business_date": business_date, "shop_timezone": record.shop.timezone, "opening_cash_cents": opening, "opening_source": source, "opening_source_id": source_id, "requires_opening": source == "missing", "requires_payment_review": payment_review,
            "sales_cash_cents": buckets["sales"], "paid_expenses_cash_cents": -buckets["expenses"], "paid_purchases_cash_cents": None if any(event["kind"] == "purchases" and event["amount"] is None for event in today) else -buckets["purchases"], "refunds_cash_cents": -buckets["refunds"], "adjustments_cash_cents": buckets["adjustments"], "expected_cash_cents": None if opening is None or payment_review else opening + sum(buckets.values()), "source_ids": source_ids, "warnings": warnings}
    version_inputs = {"breakdown": data, "events": sorted(events, key=lambda item: item["id"]), "anchors": [(str(item[3].id), str(item[0]), str(item[1]), item[2]) for item in candidates]}
    version = hashlib.sha256(json.dumps(version_inputs, default=str, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    saved = record.cash_closes.get(business_date)
    if saved:
        frozen = {name: getattr(saved, name) for name in data}
        frozen["warnings"] = list(saved.warnings)
        if set(source_ids) - set(saved.source_ids):
            frozen["warnings"].append("Additional late/backdated activity exists after this frozen close; the saved amounts have not been changed.")
        return CashClosePreview(**frozen, preview_version=saved.source_version, saved_close=saved)
    return CashClosePreview(**data, preview_version=version)
