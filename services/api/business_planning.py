"""Read-only evidence and baseline projections for business planning."""
import re
from calendar import month_name, monthrange
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from services.ai.boundary import Evidence
from .cash_close import cash_events, calculate_cash_preview
from .muse_cash import muse_cash_estimate
from .reports import sales_report


def loan_question(question):
    return bool(re.search(r"\b(?:loans?|laon|lon|chikwereti|zvikwereti)\b", question, re.I))


def planning_question(question):
    return bool(re.search(r"forecast|projection|business plan|business doing|shop doing|business overview|my (?:products|stock|inventory)|stock levels|low stock|restock", question, re.I))


def requested_month(question, today):
    """Use the most recent explicit month in the supplied conversation."""
    names = {name.lower(): number for number, name in enumerate(month_name) if name}
    pattern = r"\b(last month|this month|" + "|".join(names) + r")(?:\s+(\d{4}))?\b"
    matches = list(re.finditer(pattern, question, re.I))
    if not matches:
        return today.strftime("%Y-%m")
    match = matches[-1]
    label = match[1].lower()
    if label == "last month":
        return (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    if label == "this month":
        return today.strftime("%Y-%m")
    number = names[label]
    year = int(match[2]) if match[2] else today.year - (number > today.month)
    return f"{year:04d}-{number:02d}"


def completed_months(question):
    matches = list(re.finditer(r"\b(?:last|past|previous)\s+(1[01]|[1-9])\s+(?:full\s+)?months?\b", question, re.I))
    return int(matches[-1][1]) if matches else None


def assumed_repayment_budget(question, gross_profit_micros, months=1):
    matches = list(re.finditer(
        r"(?:set\s*(?:aside|asside)|allocate|use|assume)[^\n%]{0,40}?(\d{1,3}(?:\.\d{1,2})?)\s*%",
        question, re.I,
    ))
    if not matches or gross_profit_micros is None or gross_profit_micros <= 0:
        return None
    percent = Decimal(matches[-1][1])
    if not 0 < percent <= 100:
        return None
    amount = (Decimal(gross_profit_micros) * percent / (100_000_000 * months)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    return (percent, amount) if amount > 0 else None


def planning_snapshot(record, question, now, report_month=None):
    today = now.astimezone(ZoneInfo(record.shop.timezone)).date()
    end = today - timedelta(days=1)
    start = end - timedelta(days=29)
    historical = sales_report(record, start_date=start, end_date=end)
    selected_month = report_month or requested_month(question, today)
    months = completed_months(question)
    try:
        if months:
            year, month_index = divmod(today.year * 12 + today.month - 1 - months, 12)
            current = sales_report(
                record, start_date=today.replace(year=year, month=month_index + 1, day=1),
                end_date=today.replace(day=1) - timedelta(days=1),
            )
        else:
            current = sales_report(record, month=selected_month)
    except ValueError:
        current = None
    currency = record.shop.currency
    period = f"{start} to {end}"
    if current is None:
        message = f"No observed report is available for {selected_month}. Choose a month through {today:%Y-%m}."
        return [message], [message], (Evidence("catalogue-size", "catalogue product count", len(record.products), "products", str(today)),)
    month = f"{current['start_date']} to {current['coverage_end_date']}"
    summary = current["summary"]
    money = lambda cents: f"{currency} {cents / 100:,.2f}"
    evidence = [
        Evidence("sales-month", "recorded sales", summary["sales_total_cents"] / 100, currency, month),
        Evidence("receipts-month", "customer receipts", summary["transaction_count"], "receipts", month),
        Evidence("sheets-month", "confirmed daily sales sheets", summary["daily_summary_count"], "sheets", month),
    ]
    facts = [f"Recorded sales for {month}: {money(summary['sales_total_cents'])} across {summary['transaction_count']} customer receipts and {summary['daily_summary_count']} daily sales sheets."]
    missing = []
    profit = summary["gross_profit_micros"]
    if profit is None:
        missing.append("Complete historical product costs for gross profit.")
    else:
        facts.append(f"Gross profit before expenses: {currency} {profit / 1_000_000:,.2f}.")
        evidence.append(Evidence("gross-profit-month", "gross profit before expenses", profit / 1_000_000, currency, month))
    if loan_question(question) and not months:
        year, month_index = divmod(today.year * 12 + today.month - 4, 12)
        prior = sales_report(record, start_date=today.replace(year=year, month=month_index + 1, day=1),
                             end_date=today.replace(day=1) - timedelta(days=1))
        prior_period = f"{prior['start_date']} to {prior['coverage_end_date']}"
        totals = prior["summary"]
        evidence.append(Evidence("sales-prior-three-months", "recorded sales over the prior three complete months",
                                 totals["sales_total_cents"] / 100, currency, prior_period))
        if totals["gross_profit_micros"] is not None:
            evidence.append(Evidence("gross-profit-prior-three-months", "gross profit before expenses over the prior three complete months",
                                     totals["gross_profit_micros"] / 1_000_000, currency, prior_period))
    if loan_question(question) or re.search(r"\baf+ord\b", question, re.I):
        assumed = assumed_repayment_budget(question, profit, months or 1)
        if assumed:
            percent, amount = assumed
            facts.append(f"Your {percent}% set-aside assumption applied to average monthly gross profit gives an illustrative monthly repayment budget of {currency} {amount:,.2f} for {month}. This is a scenario, not verified cash available after expenses.")
            evidence.append(Evidence("assumed-repayment-budget", "user-assumed monthly repayment budget based on gross profit", float(amount), currency, month))
    leaders = sorted(current["products"], key=lambda item: (-item["quantity_sold"], item["product_name"]))
    if leaders:
        best = leaders[0]["quantity_sold"]
        tied = [item["product_name"] for item in leaders if item["quantity_sold"] == best]
        facts.append(f"Top by recorded units: {', '.join(tied[:5])} ({best} each).")
    products = sorted(record.products.values(), key=lambda p: (p.stock_qty, p.name, str(p.id)))
    low = [p for p in products if p.stock_qty <= 5]
    facts.append(f"{len(products)} catalogue products. {len(low)} have five units or fewer.")
    if low:
        facts.append("Low stock: " + ", ".join(f"{p.name} ({p.stock_qty})" for p in low[:5]) + ".")
    events = [event for event in cash_events(record) if start <= event["date"] <= end and event["at"] <= now]
    active = len(historical["daily"])
    horizon_match = re.search(r"(?:next|for)\s+(\d{1,3})\s*(days?|months?)\b", question, re.I)
    horizon = 30
    label = "30-day"
    if horizon_match:
        count = max(1, int(horizon_match[1]))
        if horizon_match[2].lower().startswith("month"):
            months = min(12, count)
            year, month_index = divmod(today.year * 12 + today.month - 1 + months, 12)
            month_number = month_index + 1
            boundary = today.replace(year=year, month=month_number,
                                     day=min(today.day, monthrange(year, month_number)[1]))
            horizon = (boundary - today).days
            label = f"{months}-month"
        else:
            horizon = min(360, count)
            label = f"{horizon}-day"
    forecast_period = f"{today} to {today + timedelta(days=horizon-1)}"
    forecast = []
    if active >= 7:
        sales = historical["summary"]["sales_total_cents"] * horizon / 30
        forecast.append(f"Baseline recorded sales: {money(sales)}.")
        evidence.append(Evidence("sales-projection", "baseline sales projection", sales / 100, currency, forecast_period))
        if any(event["amount"] is None for event in events):
            missing.append("Actual cash payment amounts for some purchases.")
        else:
            net = sum(event["amount"] for event in events) * horizon / 30
            forecast.append(f"Baseline net recorded cash movement: {money(net)}.")
            evidence.append(Evidence("cash-projection", "baseline net recorded cash movement", net / 100, currency, forecast_period))
    else:
        missing.append(f"At least 7 days with saved sales in the last 30 complete days for a baseline forecast. Found {active}.")
    cash = calculate_cash_preview(record, today)
    if cash.expected_cash_cents is not None:
        facts.append(f"Expected cash on hand today from recorded activity: {money(cash.expected_cash_cents)}. Confirm with a cash count.")
        evidence.append(Evidence("expected-cash-today", "expected cash on hand before cash count", cash.expected_cash_cents / 100, currency, str(today)))
    elif cash.requires_opening:
        drawer = muse_cash_estimate(record, today, today, now=now)
        estimate = drawer["estimated_ending_cash_cents"]
        if estimate is not None:
            facts.append(f"Estimated drawer cash today: {money(estimate)}. {drawer['assumption_note']}")
            evidence.append(Evidence("estimated-cash-today", "estimated drawer cash with assumed zero opening; not counted",
                                     estimate / 100, currency, str(today)))
        else:
            missing.append("Actual cash payment amounts are needed to complete the zero-opening estimate.")
    if forecast:
        facts.append(f"{label} scenario ({forecast_period}), using the daily average over {period}, including days with no saved sales. " + " ".join(forecast))
        facts.append("Cash movement covers recorded cash sales, purchases, expenses, refunds and adjustments. Unrecorded activity and future commitments can change the result.")
    evidence.append(Evidence("catalogue-size", "catalogue product count", len(products), "products", str(today)))
    normalized_question = question.casefold()
    selected = sorted(products, key=lambda p: not (
        p.name.casefold() in normalized_question or p.sku.casefold() in normalized_question
    ))[:90]
    for index, product in enumerate(selected):
        evidence.append(Evidence(f"stock-{index+1}", f"Stock on hand: {product.name} ({product.sku}), selling price {money(product.unit_price_cents)}"[:240], product.stock_qty, "units", str(today)))
    if len(products) > 90:
        missing.append("The AI snapshot includes up to 90 products, prioritizing named and low-stock items.")
    if re.search(r"my (?:products|stock|inventory)|stock levels", question, re.I):
        facts.extend(f"{p.name} ({p.sku}): {p.stock_qty} on hand, {money(p.unit_price_cents)} selling price." for p in selected)
    return facts, missing, tuple(evidence)
