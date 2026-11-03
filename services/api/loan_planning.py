"""Parse an illustrative fixed-rate monthly loan scenario from chat turns."""
import re
from decimal import Decimal, ROUND_HALF_UP

_AMOUNT = re.compile(r"(?:USD\s*|\$\s*)(\d{1,9}(?:\.\d{1,2})?)(?![\d.,%])", re.I)
_TERM = re.compile(r"\b(?:(\d{1,3})\s*(months?e?|years?)|(mwedzi|makore)\s+(\d{1,3}))\b", re.I)
_FEES = re.compile(r"\bfees?\s*(?:of|are|is|:|=)?\s*(?:USD\s*|\$\s*)?(\d{1,9}(?:\.\d{1,2})?)(?![\d.,%])|\b(?:(?:no|zero)\s+fees|hapana\s+(?:fees|muripo))\b", re.I)


def repayment_terms(message):
    """Exclude reporting windows from candidate repayment terms."""
    cleaned = re.sub(r"\b(?:last|past|previous|next)\s+\d{1,3}\s*(?:full\s+)?(?:months?|years?)\b", "", message, flags=re.I)
    return list(dict.fromkeys(
        int(match[1] or match[4]) * (12 if (match[2] or match[3]).lower().startswith(("year", "makore")) else 1)
        for match in _TERM.finditer(cleaned)
    ))


def annual_rate(message):
    match = re.search(r"\b(\d{1,3}(?:\.\d{1,3})?)\s*%\s*(?:(?:annual\s+)?(?:interest|apr)|pagore)\b", message, re.I)
    if match and not re.search(r"\b(?:monthly|per month)\b", message[match.end():].split(",")[0], re.I):
        return Decimal(match[1])
    return None


def loan_follow_up(missing, shona):
    questions = {
        "Loan amount in USD": ("How much do you want to borrow in USD, and what will you use it for?", "Munoda kukwereta marii muUSD, uye muchaishandisei?"),
        "Repayment term in months": ("Over how many months do you want to repay the loan?", "Munoda kubhadhara chikwereti mumwedzi mingani?"),
        "Annual interest rate": ("What annual interest rate did the lender quote?", "Mukweretesi ati mubereko wegore uchava zvikamu zvingani kubva muzana?"),
        "Upfront fees, or say no fees": ("How much will the lender charge in upfront fees, if any?", "Mukweretesi achachaja marii pakutanga, kana kuti hapana muripo?"),
    }
    return questions[missing[0]][int(shona)]


def loan_scenario(messages, currency):
    term = rate = fees = principal = None
    for message in messages:
        fee = _FEES.search(message)
        if fee:
            fees = Decimal(fee[1] or "0")
        amount = _AMOUNT.search(_FEES.sub("", message))
        if amount is None and currency == "USD":
            amount = re.search(
                r"\b(?:i (?:need|want)|borrow)\s+(\d{1,9}(?:\.\d{1,2})?)(?![\d.,%]|\s*(?:months?|years?|days?)\b)",
                message, re.I,
            )
        if amount:
            principal = Decimal(amount[1])
        terms = repayment_terms(message)
        if terms:
            term = terms[0]
        quoted_rate = annual_rate(message)
        if quoted_rate is not None:
            rate = quoted_rate
    missing = []
    if principal is None or principal <= 0 or currency != "USD":
        missing.append("Loan amount in USD")
    if term is None or not 1 <= term <= 360:
        missing.append("Repayment term in months")
    if rate is None or not 0 <= rate <= 100:
        missing.append("Annual interest rate")
    if fees is None:
        missing.append("Upfront fees, or say no fees")
    if missing:
        return None, missing
    monthly_rate = rate / 1200
    payment = principal / term if not monthly_rate else principal * monthly_rate / (1 - (1 + monthly_rate) ** -term)
    cents = lambda value: f"USD {value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"
    return (
        f"Illustrative repayment for {cents(principal)} over {term} months at {rate}% annual interest: "
        f"{cents(payment)} per month, plus {cents(fees)} in upfront fees. "
        f"Estimated total paid including fees: {cents(payment * term + fees)}. "
        "This assumes a fixed annual rate, a reducing balance and monthly payments. "
        "Compare the estimate with the lender’s repayment schedule and your available cash after expenses.",
        [],
    )

def borrowing_scenario(messages, currency):
    """Estimate principal supported by an explicitly supplied monthly payment."""
    budget = rate = fees = None
    terms = []
    for message in messages:
        clean = _FEES.sub("", message)
        match = re.search(r"(?:USD\s*|\$\s*)(\d{1,9}(?:\.\d{1,2})?)\s*(?:per month|/month|monthly)\b", clean, re.I)
        if match:
            budget = Decimal(match[1])
        requested_terms = repayment_terms(message)
        if requested_terms:
            terms = requested_terms
        quoted_rate = annual_rate(message)
        if quoted_rate is not None:
            rate = quoted_rate
        fee = _FEES.search(message)
        if fee:
            fees = Decimal(fee[1] or "0")
    missing = []
    if budget is None or budget <= 0 or currency != "USD":
        missing.append("Monthly repayment budget")
    if not terms or any(not 1 <= term <= 360 for term in terms):
        missing.append("Repayment term in months")
    if rate is None or not 0 <= rate <= 100:
        missing.append("Annual interest rate")
    if fees is None:
        missing.append("Upfront fees, or say no fees")
    if missing:
        return None, missing
    monthly_rate = rate / 1200
    from decimal import ROUND_DOWN
    comparisons = []
    for term in terms[:12]:
        principal = budget * term if not monthly_rate else budget * (1 - (1 + monthly_rate) ** -term) / monthly_rate
        principal = principal.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        comparisons.append(f"{term} months: USD {principal:,.2f}")
    return (
        f"Illustrative principal by term at USD {budget:,.2f} per month and {rate}% annual interest:\n"
        + "\n".join(comparisons)
        + f"\nUpfront fees: USD {fees:,.2f}. Assumes a fixed rate, reducing balance and monthly payments.",
        [],
    )
