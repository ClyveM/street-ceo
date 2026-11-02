"""Narrow repository-grounded answers to straightforward sales questions."""
from datetime import date, datetime, timedelta
import re
from zoneinfo import ZoneInfo

from .reports import sales_report


def repository_sales_answer(question, record):
    text = question.lower().strip()
    if any(word in text for word in ("profit", "margin", "cogs", "expense", "forecast", "predict", "why", "recommend", "should", "compare")):
        return None
    ranking = bool(re.search(r"(?:best[ -]?selling|most[ -]?selling|top[ -]?selling|sell(?:s|ing)? (?:the )?most|highest.*(?:revenue|sales))", text))
    ranking = ranking or bool(re.search(r"top\s+(?:product|item)", text))
    ranking = ranking or bool(re.search(r"(?:product|item).*sell(?:s|ing)?\s+best", text))
    totals = bool(re.search(r"(?:total sales|sales total|sales summary|how much.*(?:sell|sold|sales)|how many.*(?:transactions|sales)|what.*sales.*(?:today|month))", text))
    if not ranking and not totals:
        return None
    if re.search(r"\b(?:cash|bank|refund|net)\b", text):
        return None
    if not ranking and (re.search(r"\b(?:cash|bank|refund|net|product|item)\b", text) or
                        any(product.name.lower() in text or product.sku.lower() in text for product in record.products.values())):
        return None
    def result(answer, title, ids=(), missing=()):
        return dict(status="needs_data" if missing else "answered", answer=answer, title=title,
                    evidence_ids=list(ids), missing_data=list(missing), source="repository", confidence=1.0)
    today = datetime.now(ZoneInfo(record.shop.timezone)).date()
    options = {}
    custom = re.search(r"(?:between|from)\s+(\d{4}-\d{2}-\d{2})\s+(?:and|to)\s+(\d{4}-\d{2}-\d{2})", text)
    past = re.search(r"(?:last|past)\s+(\d+)\s+days?", text)
    month = re.search(r"\b(\d{4}-\d{2})\b", text)
    if custom:
        try:
            options = dict(start_date=date.fromisoformat(custom[1]), end_date=date.fromisoformat(custom[2]))
        except ValueError:
            return result("Please supply valid dates as YYYY-MM-DD.", "Choose a sales period", missing=["valid sales date range"])
    elif "yesterday" in text:
        options = dict(start_date=today-timedelta(days=1), end_date=today-timedelta(days=1))
    elif "today" in text:
        options = dict(preset="last1")
    elif past:
        if not 1 <= int(past[1]) <= 366:
            return result("Please choose between 1 and 366 days.", "Choose a sales period", missing=["valid observed sales period"])
        options = dict(start_date=today-timedelta(days=int(past[1])-1), end_date=today)
    elif "last month" in text:
        options = dict(month=(today.replace(day=1)-timedelta(days=1)).strftime('%Y-%m'))
    elif month:
        options = dict(month=month[1])
    elif any(word in text for word in ("week", "year", "all time", "all-time", "since", "between", "from", "last", "past", "tomorrow", "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december")) or re.search(r"\b\d{4}\b", text):
        return result("Please choose today, yesterday, this month, last month, last N days, or a date range such as between 2026-10-01 and 2026-10-31.", "Choose a sales period", missing=["supported explicit sales period"])
    try:
        report = sales_report(record, **options)
    except (ValueError, OverflowError):
        return result("Please choose an observed sales period of 1–366 days with valid dates.", "Choose a sales period", missing=["valid observed sales period"])
    period = f"{report['start_date']} to {report['coverage_end_date']} ({report['shop_timezone']})"
    if not options:
        period = "this month to date, " + period
    suffix = f"{report['start_date']}_to_{report['coverage_end_date']}_{report['shop_timezone'].replace('/', '_')}"
    ids = [f"sales-{suffix}", f"transactions-{suffix}"]
    summary = report['summary']
    money = lambda cents: f"{record.shop.currency} {cents / 100:.2f}"
    disclaimer = " Stock-only Undo does not reduce these gross recorded sales." if report['stock_reversal_count'] else ""
    if not ranking:
        sheets=f" Plus {summary['daily_summary_count']} daily sales sheet(s), included in the sales amount but not the customer transaction count." if summary.get('daily_summary_count') else ''
        return result(f"Recorded gross sales for {period}: {money(summary['sales_total_cents'])} across {summary['transaction_count']} transaction(s) (customer receipts).{sheets}{disclaimer}", "Recorded sales summary", ids)
    products = report['products']
    if not products:
        return result(f"No sales were recorded for {period}, so there is no best-selling product yet.", "No recorded sales", ids)
    revenue = any(word in text for word in ("revenue", "by value", "by amount", "sales value"))
    metric = 'revenue_cents' if revenue else 'quantity_sold'
    if revenue and any(row[metric] is None for row in products):
        return result(f"I cannot reliably rank products by revenue for {period}: some older receipts do not save product-level amounts. I can rank by quantity sold instead.", "Product revenue is incomplete", ids, ["saved product-level revenue for legacy receipts"])
    best = max(row[metric] for row in products)
    winners = [row for row in products if row[metric] == best]
    labels = ', '.join(row['product_name'] for row in winners)
    amount = money(best) if revenue else f"{best} unit(s)"
    title = "Top products are tied" if len(winners) > 1 else "Best-selling product"
    label_note = " Some labels come from the current catalogue because older receipts lack saved names." if any(row['label_source'] not in {'latest_receipt_snapshot','daily_summary_snapshot'} for row in winners) else ""
    return result(f"{'Tied for best-selling' if len(winners)>1 else 'Best-selling'} by {'recorded revenue' if revenue else 'quantity sold'} for {period}: {labels} — {amount} each.{label_note}{disclaimer}", title, ids)
