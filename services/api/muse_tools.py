"""Strict read-only tools for one authenticated shop snapshot."""
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .cash_close import calculate_cash_preview, cash_events
from .muse_cash import muse_cash_estimate, recorded_cash_movements
from .paper_sales import confirmed_batches
from .reports import sales_report


class Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Period(Args):
    start_date: date
    end_date: date

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def iso_date(cls, value):
        if type(value) is date:
            return value
        if not isinstance(value, str) or len(value) != 10 or str(date.fromisoformat(value)) != value:
            raise ValueError("Use an ISO date in YYYY-MM-DD format.")
        return value


class Sales(Period):
    group_by: Literal["summary", "day", "month"] = "summary"
    offset: int = Field(0, ge=0, le=400)


class Page(Args):
    offset: int = Field(0, ge=0, le=10000)
    limit: int = Field(20, ge=1, le=40)
    search: str = Field("", max_length=80)


class ProductPeriod(Period, Page):
    pass


class Forecast(Period):
    horizon_days: int = Field(30, ge=1, le=366)


class ProfitBudget(Period):
    set_aside_percent: float = Field(gt=0, le=100, allow_inf_nan=False)
    months: int = Field(ge=1, le=12, strict=True)


class Finance(Args):
    monthly_budget_cents: int | None = Field(default=None, gt=0, le=100_000_000, strict=True)
    gross_profit_budget: ProfitBudget | None = None
    annual_interest_percent: float = Field(ge=0, le=100, allow_inf_nan=False)
    terms_months: list[Annotated[int, Field(strict=True, ge=1, le=360)]] = Field(min_length=1, max_length=12)
    upfront_fees_cents: int = Field(ge=0, le=100_000_000, strict=True)


def toolset(record):
    zone = ZoneInfo(record.shop.timezone)
    today = datetime.now(zone).date()
    currency = record.shop.currency

    def bounds(args):
        if args.start_date > args.end_date or args.end_date > today:
            raise ValueError("Choose an ordered range through the current shop date.")
        if (args.end_date - args.start_date).days >= 366:
            raise ValueError("Maximum report range is 366 days. Use successive ranges for longer history.")
        return args.start_date, args.end_date

    def report(args):
        start, end = bounds(args)
        return sales_report(record, start_date=start, end_date=end)

    def metadata(values):
        dates = sorted(values)
        months = sorted({str(day)[:7] for day in dates})
        return {"record_count": len(dates), "earliest": dates[0].isoformat() if dates else None,
                "latest": dates[-1].isoformat() if dates else None,
                "months_with_records": months[-36:],
                "coverage": "Dates without records may be missing data. Coverage is not independently verified."}

    def discover(_):
        receipts = {sale.id: sale for _, sale in record.idempotent_sales.values()}
        batches = list(confirmed_batches(record))
        return {"currency": currency, "shop_today": str(today), "sales": {
                    **metadata([sale.created_at.astimezone(zone).date() for sale in receipts.values()]
                               + [batch.business_date for batch in batches]),
                    "receipts": len(receipts), "confirmed_daily_sheets": len(batches),
                    "granularity": ["day", "month", "product"],
                    "metrics": ["sales_total_cents", "cogs_micros", "gross_profit_micros"],
                    "unknown_receipt_cogs_count": sum(sale.cogs_micros is None for sale in receipts.values()),
                },
                "expenses": metadata([e.occurred_on for e in record.expenses.values() if e.status == "confirmed"]),
                "purchases": metadata([p.purchase_date for p in record.purchases.values() if p.status == "confirmed"]),
                "inventory": {"products": len(record.products), "as_of": str(today)},
                "cashflow": metadata([event["date"] for event in cash_events(record)])}

    def sales(args):
        data = report(args)
        result = {key: data[key] for key in ("start_date", "end_date", "currency", "summary", "warnings")}
        if args.group_by != "summary":
            rows = data["daily" if args.group_by == "day" else "monthly"]
            result.update(rows=rows[args.offset:args.offset+31], total_rows=len(rows),
                          next_offset=args.offset+31 if args.offset+31 < len(rows) else None)
        return result

    def inventory(args):
        rows = sorted(record.products.values(), key=lambda p: (p.stock_qty, p.sku))
        rows = [p for p in rows if args.search.casefold() in (p.name + " " + p.sku).casefold()]
        return {"currency": currency, "as_of": str(today), "total_rows": len(rows), "rows": [
            {"sku": p.sku, "product": p.name, "stock_qty": p.stock_qty,
             "unit_price_cents": p.unit_price_cents, "unit_cost_micros": p.unit_cost_micros}
            for p in rows[args.offset:args.offset+args.limit]]}

    def performance(args):
        data = report(args)
        rows = [p for p in data["products"] if args.search.casefold() in
                (p["product_name"] + " " + str(p.get("sku", ""))).casefold()]
        return {"currency": currency, "start_date": data["start_date"], "end_date": data["end_date"],
                "total_rows": len(rows), "rows": rows[args.offset:args.offset+args.limit], "warnings": data["warnings"]}

    def spending(args, kind):
        start, end = bounds(args)
        records = record.expenses.values() if kind == "expenses" else record.purchases.values()
        totals = defaultdict(int)
        count = 0
        for item in records:
            day = item.occurred_on if kind == "expenses" else item.purchase_date
            if item.status == "confirmed" and start <= day <= end:
                totals[str(day)[:7]] += item.amount_cents if kind == "expenses" else item.total_cost_micros
                count += 1
        return {"currency": currency, "start_date": str(start), "end_date": str(end), "record_count": count,
                "unit": "cents" if kind == "expenses" else "micros",
                "recorded_total": sum(totals.values()), "by_month": dict(totals),
                "coverage": "Confirmed records by posting date. Completeness and period allocation are unverified."}

    def cashflow(args):
        start, end = bounds(args)
        totals, missing = recorded_cash_movements(record, start, end)
        return {"currency": currency, "start_date": str(start), "end_date": str(end),
                "recorded_movements_cents": totals, "unvalued_movements": missing,
                "net_recorded_movement_cents": sum(totals.values()) if not missing else None,
                "coverage": "Recorded drawer cash movements only. No bank settlement is inferred.",
                **muse_cash_estimate(record, start, end, movements=(totals, missing))}

    def metrics(args):
        result = sales(Sales(start_date=args.start_date, end_date=args.end_date))
        expenses = spending(args, "expenses")
        result["recorded_expenses_cents"] = expenses["recorded_total"]
        result["confirmed_expense_count"] = expenses["record_count"]
        result["net_profit_micros"] = None
        result["expense_coverage"] = "Expense completeness and period allocation are unverified."
        return result

    def trends(args):
        result = sales(Sales(start_date=args.start_date, end_date=args.end_date, group_by="month"))
        rows = result["rows"]
        changes = []
        for prior, latest in zip(rows, rows[1:]):
            if prior["sales_total_cents"]:
                changes.append({"from": prior["month"], "to": latest["month"], "change_percent":
                                round((latest["sales_total_cents"] - prior["sales_total_cents"])
                                      * 100 / prior["sales_total_cents"], 2)})
        result["changes"] = changes
        result["comparison_warning"] = "First and last months may be partial. Changes do not establish causes."
        return result

    def forecast(args):
        data = report(args)
        days = (args.end_date - args.start_date).days + 1
        observed = len(data["daily"])
        result = {"currency": currency, "baseline_start": data["start_date"], "baseline_end": data["end_date"],
                  "observed_sales_days": observed, "baseline_calendar_days": days,
                  "forecast_start": str(today + timedelta(days=1)),
                  "forecast_end": str(today + timedelta(days=args.horizon_days)),
                  "method": "Recorded daily mean over selected calendar days. Missing dates may bias results.",
                  "projection_sales_cents": None}
        if observed >= 7 and args.end_date < today:
            result["projection_sales_cents"] = int((Decimal(data["summary"]["sales_total_cents"])
                                                   * args.horizon_days / days).quantize(Decimal(1), rounding=ROUND_HALF_UP))
        else:
            result["missing_data"] = "Choose a completed baseline with at least seven days of recorded sales."
        preview = calculate_cash_preview(record, today)
        drawer = muse_cash_estimate(record, args.start_date if preview.requires_opening else today, today)
        counted_today = drawer["recorded_ending_cash_count_cents"]
        starting_cash = counted_today if counted_today is not None else drawer["estimated_ending_cash_cents"]
        cash_basis = (
            "Today’s recorded closing count is used as the starting balance. "
            if counted_today is not None else drawer["assumption_note"] + " "
        )
        result["cash_scenario"] = {
            "cash_as_of": str(today),
            "cash_estimate_period_start": str(args.start_date if preview.requires_opening else today),
            "starting_cash_cents": starting_cash,
            "starting_cash_basis": "counted_close" if counted_today is not None else drawer["opening_basis"],
            "projected_cash_movement_cents": None,
            "projected_ending_cash_cents": None,
            "assumption_note": cash_basis + "Future cash movement uses a baseline average, not a verified balance.",
        }
        cash_totals, missing = recorded_cash_movements(record, args.start_date, args.end_date)
        if observed >= 7 and args.end_date < today and not missing:
            projected = int((Decimal(sum(cash_totals.values())) * args.horizon_days / days).quantize(
                Decimal(1), rounding=ROUND_HALF_UP,
            ))
            result["cash_scenario"]["projected_cash_movement_cents"] = projected
            if starting_cash is not None:
                result["cash_scenario"]["projected_ending_cash_cents"] = starting_cash + projected
        return result

    def financing(args):
        if (args.monthly_budget_cents is None) == (args.gross_profit_budget is None):
            raise ValueError("Supply exactly one explicit monthly budget or gross-profit set-aside scenario.")
        basis = {"type": "user_supplied_budget"}
        if args.gross_profit_budget is not None:
            selected = args.gross_profit_budget
            start, end = bounds(selected)
            month_count = (end.year - start.year) * 12 + end.month - start.month + 1
            if start.day != 1 or (end + timedelta(days=1)).day != 1 or month_count != selected.months or end >= today:
                raise ValueError("Gross-profit set-aside requires complete calendar months matching the stated count.")
            financials = report(selected)["summary"]
            profit = financials["gross_profit_micros"]
            if profit is None or profit <= 0:
                return {"currency": currency, "scenarios": [],
                        "missing_data": "A positive recorded gross profit with complete cost data is required."}
            budget = (Decimal(profit) * Decimal(str(selected.set_aside_percent)) /
                      (1_000_000 * selected.months)).quantize(Decimal(1), rounding=ROUND_DOWN)
            basis = {"type": "illustrative_gross_profit_set_aside", "period_start": str(start),
                     "period_end": str(end), "gross_profit_micros": profit,
                     "set_aside_percent": selected.set_aside_percent, "months": selected.months,
                     "coverage": "Gross profit before operating expenses is not available repayment cash."}
        else:
            budget = Decimal(args.monthly_budget_cents)
        rate = Decimal(str(args.annual_interest_percent)) / 1200
        return {"currency": currency, "monthly_budget_cents": int(budget), "budget_basis": basis,
                "annual_interest_percent": args.annual_interest_percent, "upfront_fees_cents": args.upfront_fees_cents,
                "assumption": "User-supplied repayment budget and fixed annual reducing-balance interest. Fees are separate.",
                "scenarios": [{"months": term, "illustrative_principal_cents": int((
                    budget * (1 - (1 + rate) ** -term) / rate if rate else budget * term
                ).quantize(Decimal(1), rounding=ROUND_DOWN))} for term in dict.fromkeys(args.terms_months)]}

    def bind(model, handler):
        return model.model_json_schema(), lambda raw: handler(model.model_validate(raw))

    return {
        "discover_business_data": bind(Args, discover),
        "query_sales": bind(Sales, sales),
        "query_inventory": bind(Page, inventory),
        "query_product_performance": bind(ProductPeriod, performance),
        "query_expenses": bind(Period, lambda args: spending(args, "expenses")),
        "query_purchases": bind(Period, lambda args: spending(args, "purchases")),
        "query_cashflow": bind(Period, cashflow),
        "calculate_financial_metrics": bind(Period, metrics),
        "analyze_trends": bind(Period, trends),
        "run_forecast": bind(Forecast, forecast),
        "assess_financing": bind(Finance, financing),
    }
