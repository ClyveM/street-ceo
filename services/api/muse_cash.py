"""Read-only cash scenarios for Muse. No accounting anchors are created."""
from collections import defaultdict
from datetime import datetime, timezone

from .cash_close import calculate_cash_preview, cash_events


def recorded_cash_movements(record, start, end, *, now=None):
    cutoff = now or datetime.now(timezone.utc)
    totals = defaultdict(int)
    missing = 0
    for event in cash_events(record):
        if not start <= event["date"] <= end or event["at"] > cutoff:
            continue
        if event["amount"] is None:
            missing += 1
        else:
            totals[event["kind"]] += event["amount"]
    return dict(totals), missing


def muse_cash_estimate(record, start, end, *, now=None, movements=None):
    opening = calculate_cash_preview(record, start)
    totals, missing = movements if movements is not None else recorded_cash_movements(record, start, end, now=now)
    assumed_zero = opening.opening_cash_cents is None and opening.requires_opening
    used_opening = 0 if assumed_zero else opening.opening_cash_cents
    expected = used_opening + sum(totals.values()) if used_opening is not None and not missing else None
    if start == end and opening.saved_close is not None:
        # A saved close is frozen, even when later/backdated events are visible.
        expected = opening.expected_cash_cents
        assumed_zero = False
        used_opening = opening.opening_cash_cents
    close = record.cash_closes.get(end) or record.day_closes.get(end)
    note = (
        "Opening cash was not recorded. This estimate starts at zero for the selected period and uses recorded cash movements only."
        if assumed_zero else
        "Uses the recorded opening anchor for the selected period. Expected cash is calculated, not a physical count."
    )
    if used_opening is None:
        note = "The starting cash anchor cannot be valued from complete recorded movements."
    if expected is None:
        note += " An unresolved cash amount prevents a complete estimate."
    return {
        "recorded_opening_cash_cents": opening.opening_cash_cents,
        "opening_cash_used_cents": used_opening,
        "opening_basis": "assumed_zero" if assumed_zero else opening.opening_source,
        "estimated_ending_cash_cents": expected,
        "recorded_ending_cash_count_cents": close.cash_counted_cents if close else None,
        "assumption_note": note + " Bank sales do not enter drawer cash.",
    }
