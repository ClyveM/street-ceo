"""Read-only sales reports from saved receipts, never current-price estimates."""
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def _gross_profit(revenue_cents, cogs_micros):
    """Exact saved-cost gross profit; nearest basis point, ties away from zero."""
    if revenue_cents is None or cogs_micros is None:
        return {"gross_profit_micros": None, "margin_bps": None}
    revenue_micros = revenue_cents * 10_000
    profit = revenue_micros - cogs_micros
    if revenue_micros == 0:
        margin = None
    else:
        numerator = abs(profit) * 10_000
        quotient, remainder = divmod(numerator, revenue_micros)
        rounded = quotient + (2 * remainder >= revenue_micros)
        margin = -rounded if profit < 0 else rounded
    return {"gross_profit_micros": profit, "margin_bps": margin}


def sales_report(record, start_date=None, end_date=None, preset=None, month=None):
    zone = ZoneInfo(record.shop.timezone)
    today = datetime.now(zone).date()
    now = datetime.now(timezone.utc)
    coverage = "historical_or_selected_range"
    if start_date is not None or end_date is not None:
        if start_date is None or end_date is None or preset is not None or month is not None:
            raise ValueError("Supply both custom dates or one preset/month")
    elif preset in {"last1", "last20", "last90"}:
        if month is not None:
            raise ValueError("Month cannot accompany a day preset")
        end_date = today
        start_date = today - timedelta(days=int(preset[4:]) - 1)
    else:
        if preset not in {None, "month"}:
            raise ValueError("Unsupported report preset")
        try:
            first = date.fromisoformat((month or today.strftime("%Y-%m")) + "-01")
        except ValueError as exc:
            raise ValueError("Month must be YYYY-MM") from exc
        start_date = first
        end_date = (first.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        if first > today:
            raise ValueError("Future months have no observed sales coverage")
        if first.year == today.year and first.month == today.month:
            end_date = today
            coverage = "current_month_to_date"
    if end_date < start_date or (end_date - start_date).days >= 366:
        raise ValueError("Report range must contain 1–366 inclusive days")
    if start_date > today:
        raise ValueError("Future-only ranges have no observed sales coverage")
    start = datetime.combine(start_date, datetime.min.time(), zone).astimezone(timezone.utc)
    end = datetime.combine(end_date + timedelta(days=1), datetime.min.time(), zone).astimezone(timezone.utc)
    unique = {sale.id: sale for _, sale in record.idempotent_sales.values()}
    receipts = sorted((sale for sale in unique.values() if start <= sale.created_at < end and sale.created_at <= now), key=lambda sale: sale.created_at)
    from .paper_sales import confirmed_batches
    batches = [item for item in confirmed_batches(record) if start_date <= item.business_date <= min(end_date,today) and item.confirmed_at and item.confirmed_at <= now]
    daily = defaultdict(lambda: {"sales_total_cents": 0, "transaction_count": 0, "daily_summary_count": 0})
    monthly = defaultdict(lambda: {"sales_total_cents": 0, "transaction_count": 0, "daily_summary_count": 0})
    products = {}
    warnings = []
    if end_date > today:
        coverage = "observed_to_date_not_forecast"
        warnings.append("Selected range extends beyond today; only observed receipts through the as-of time are included.")
    unknown_cogs = 0
    known_cogs = 0
    unallocated_revenue = 0
    tenders = defaultdict(int)
    for sale in receipts:
        business_date = sale.created_at.astimezone(zone).date().isoformat()
        for bucket in (daily[business_date], monthly[business_date[:7]]):
            bucket["sales_total_cents"] += sale.total_cents
            bucket["transaction_count"] += 1
        tenders[sale.tender] += sale.total_cents
        if sale.cogs_micros is None:
            unknown_cogs += 1
        else:
            known_cogs += sale.cogs_micros
        snapshots = {line.product_id: line for line in sale.receipt_lines}
        valid_snapshots = len(snapshots) == len(sale.lines) and all(line.product_id in snapshots and snapshots[line.product_id].quantity == line.quantity for line in sale.lines) and sum(line.line_total_cents for line in snapshots.values()) == sale.total_cents
        for line in sale.lines:
            current = record.products.get(line.product_id)
            snapshot = snapshots.get(line.product_id) if valid_snapshots else None
            item = products.setdefault(str(line.product_id), {"product_id": str(line.product_id), "product_name": current.name if current else str(line.product_id), "sku": current.sku if current else None, "label_source": "current_catalogue" if current else "product_id", "quantity_sold": 0, "known_revenue_cents": 0, "unknown_revenue_line_count": 0, "known_cogs_micros": 0, "unknown_cogs_line_count": 0})
            if snapshot:
                item.update(product_name=snapshot.product_name, sku=snapshot.sku, label_source="latest_receipt_snapshot")
            item["quantity_sold"] += line.quantity
            revenue = snapshot.line_total_cents if snapshot else (sale.total_cents if len(sale.lines) == 1 else None)
            cost = snapshot.line_cogs_micros if snapshot else (sale.cogs_micros if len(sale.lines) == 1 else None)
            if revenue is None:
                item["unknown_revenue_line_count"] += 1
            else:
                item["known_revenue_cents"] += revenue
            if cost is None:
                item["unknown_cogs_line_count"] += 1
            else:
                item["known_cogs_micros"] += cost
        if not valid_snapshots and len(sale.lines) > 1:
            unallocated_revenue += sale.total_cents
    for batch in batches:
        business_date=batch.business_date.isoformat()
        for bucket in (daily[business_date], monthly[business_date[:7]]):
            bucket['sales_total_cents'] += batch.total_cents
            bucket['daily_summary_count'] += 1
        tenders['cash'] += batch.cash_cents
        tenders['bank'] += batch.bank_cents
        for line in batch.lines:
            item=products.setdefault(str(line.product_id), {'product_id':str(line.product_id),'product_name':line.product_name,'sku':line.sku,'label_source':'daily_summary_snapshot','quantity_sold':0,'known_revenue_cents':0,'unknown_revenue_line_count':0,'known_cogs_micros':0,'unknown_cogs_line_count':0})
            item.update(product_name=line.product_name,sku=line.sku,label_source='daily_summary_snapshot')
            item['quantity_sold'] += line.quantity
            item['known_revenue_cents'] += line.line_total_cents
            item['unknown_cogs_line_count'] += 1
    for item in products.values():
        item["revenue_cents"] = None if item["unknown_revenue_line_count"] else item["known_revenue_cents"]
        item["cogs_micros"] = None if item["unknown_cogs_line_count"] else item["known_cogs_micros"]
        item.update(_gross_profit(item["revenue_cents"], item["cogs_micros"]))
    reversals = [item for item in record.voice_sale_reversals.values() if start <= item.created_at < end]
    if reversals:
        warnings.append("Stock-only reversals are listed separately; they do not establish a cash refund or reduce gross sales.")
    if unallocated_revenue:
        warnings.append("Legacy multi-product receipts lack line prices; product revenue is partial/unknown, never estimated from current prices.")
    if unknown_cogs:
        warnings.append("Some saved receipt costs are unknown; complete COGS/profit cannot be inferred from current product costs.")
    if batches:
        warnings.append('Daily sales sheets are separate summaries, not customer transactions. Their historical COGS is unknown; gross profit is incomplete.')
    if any(item["label_source"] not in {"latest_receipt_snapshot", "daily_summary_snapshot"} for item in products.values()):
        warnings.append("Some product labels use the current catalogue because the old receipt did not save a label.")
    return {"start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "coverage_end_date": min(end_date, today).isoformat(), "coverage": coverage, "as_of": now.isoformat(), "shop_timezone": record.shop.timezone, "currency": record.shop.currency,
            "summary": {"sales_total_cents": sum(sale.total_cents for sale in receipts)+sum(batch.total_cents for batch in batches), "transaction_count": len(receipts), "daily_summary_count":len(batches), "cash_sales_cents": tenders["cash"], "bank_sales_cents": tenders["bank"], "other_tender_sales_cents": sum(value for key, value in tenders.items() if key not in {"cash", "bank"}), "cogs_micros": None if unknown_cogs or batches else known_cogs, "known_cogs_micros": known_cogs, "missing_cogs_sale_count": unknown_cogs, "missing_cogs_daily_summary_count":len(batches), "unallocated_product_revenue_cents": unallocated_revenue, **_gross_profit(sum(sale.total_cents for sale in receipts)+sum(batch.total_cents for batch in batches), None if unknown_cogs or batches else known_cogs)},
            "daily": [{"business_date": key, **value} for key, value in sorted(daily.items())], "monthly": [{"month": key, **value} for key, value in sorted(monthly.items())], "products": sorted(products.values(), key=lambda item: item["product_id"]), "stock_reversal_count": len(reversals), "warnings": warnings}
