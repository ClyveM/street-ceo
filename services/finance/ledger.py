"""Deterministic, auditable double-entry ledger for the MVP.

The service is intentionally persistence-agnostic.  Hwaro can place a database
repository around these pure posting rules without changing their accounting
meaning.  Amounts are Decimal values in currency units; API adapters may
convert integer minor units at their boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Iterable, Mapping
from zoneinfo import ZoneInfo


ZERO = Decimal("0")


class Account(str, Enum):
    CASH = "asset:cash"
    BANK = "asset:bank"
    INVENTORY = "asset:inventory"
    SALES_REVENUE = "income:sales"
    COGS = "expense:cogs"
    OPERATING_EXPENSE = "expense:operating"
    STOCK_LOSS = "expense:stock_loss"
    OWNER_CAPITAL = "equity:owner_capital"
    OWNER_DRAWING = "equity:owner_drawing"
    OPENING_BALANCE = "equity:opening_balance"
    UNPAID_EXPENSE = "liability:unpaid_expense"


class Tender(str, Enum):
    CASH = "cash"
    BANK = "bank"

    @property
    def account(self) -> Account:
        return Account.CASH if self is Tender.CASH else Account.BANK


def _money(value: Decimal | int | str) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("amount must be a valid decimal") from exc
    if not amount.is_finite() or amount < ZERO:
        raise ValueError("amount must be finite and non-negative")
    return amount


def _timestamp(value: datetime | None) -> datetime:
    result = value or datetime.now(timezone.utc)
    if result.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return result.astimezone(timezone.utc)


@dataclass(frozen=True)
class Posting:
    account: Account
    debit: Decimal = ZERO
    credit: Decimal = ZERO

    def __post_init__(self) -> None:
        debit, credit = _money(self.debit), _money(self.credit)
        if (debit == ZERO) == (credit == ZERO):
            raise ValueError("a posting must contain exactly one non-zero debit or credit")
        object.__setattr__(self, "debit", debit)
        object.__setattr__(self, "credit", credit)


@dataclass(frozen=True)
class JournalEntry:
    entry_id: str
    shop_id: str
    currency: str
    source_type: str
    source_id: str
    actor: str
    occurred_at: datetime
    recorded_at: datetime
    postings: tuple[Posting, ...]
    warnings: tuple[str, ...] = ()
    reversal_of: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    @property
    def total_debits(self) -> Decimal:
        return sum((posting.debit for posting in self.postings), ZERO)

    @property
    def total_credits(self) -> Decimal:
        return sum((posting.credit for posting in self.postings), ZERO)

    @property
    def balanced(self) -> bool:
        return self.total_debits == self.total_credits


@dataclass(frozen=True)
class DailyClose:
    shop_id: str
    business_date: date
    timezone: str
    opening: Mapping[Tender, Decimal]
    sales: Mapping[Tender, Decimal]
    refunds: Mapping[Tender, Decimal]
    expenses: Mapping[Tender, Decimal]
    purchases: Mapping[Tender, Decimal]
    owner_drawings: Mapping[Tender, Decimal]
    owner_injections: Mapping[Tender, Decimal]
    expected: Mapping[Tender, Decimal]
    actual: Mapping[Tender, Decimal | None]
    variance: Mapping[Tender, Decimal | None]
    warnings: tuple[str, ...]
    locked_at: datetime


class Ledger:
    """In-memory journal with append-only posting and close semantics."""

    def __init__(self, *, shop_id: str, currency: str = "USD") -> None:
        if not shop_id.strip():
            raise ValueError("shop_id is required")
        if len(currency.strip()) != 3:
            raise ValueError("currency must be a three-letter code")
        self.shop_id = shop_id
        self.currency = currency.upper()
        self.entries: list[JournalEntry] = []
        self.closes: dict[date, DailyClose] = {}
        self._next_entry = 1

    def _append(
        self,
        *,
        source_type: str,
        source_id: str,
        actor: str,
        occurred_at: datetime,
        postings: Iterable[Posting],
        warnings: Iterable[str] = (),
        reversal_of: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> JournalEntry:
        postings = tuple(postings)
        if not source_id.strip() or not actor.strip():
            raise ValueError("source_id and actor are required")
        if not postings:
            raise ValueError("an entry needs postings")
        entry = JournalEntry(
            entry_id=f"JE-{self._next_entry:06d}",
            shop_id=self.shop_id,
            currency=self.currency,
            source_type=source_type,
            source_id=source_id,
            actor=actor,
            occurred_at=_timestamp(occurred_at),
            recorded_at=datetime.now(timezone.utc),
            postings=postings,
            warnings=tuple(sorted(set(warnings))),
            reversal_of=reversal_of,
            metadata=dict(metadata or {}),
        )
        if not entry.balanced:
            raise ValueError("journal entry is not balanced")
        self.entries.append(entry)
        self._next_entry += 1
        return entry

    @staticmethod
    def _tender(tender: Tender | str) -> Tender:
        try:
            return tender if isinstance(tender, Tender) else Tender(tender.lower())
        except ValueError as exc:
            raise ValueError("tender must be cash or bank") from exc

    def balance(self, account: Account) -> Decimal:
        return sum((p.debit - p.credit for e in self.entries for p in e.postings if p.account == account), ZERO)

    def balances(self) -> dict[Account, Decimal]:
        return {account: self.balance(account) for account in Account}

    def sale(
        self,
        *,
        source_id: str,
        actor: str,
        occurred_at: datetime,
        amount: Decimal | int | str,
        tender: Tender | str,
        cogs: Decimal | int | str | None,
        quantity: int,
        unit_price: Decimal | int | str | None = None,
    ) -> JournalEntry:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        tender_value = self._tender(tender)
        revenue = _money(amount)
        postings = [Posting(tender_value.account, debit=revenue), Posting(Account.SALES_REVENUE, credit=revenue)]
        warnings: list[str] = []
        if cogs is None:
            warnings.append("missing_cost_of_sales")
        else:
            cost = _money(cogs)
            postings.extend((Posting(Account.COGS, debit=cost), Posting(Account.INVENTORY, credit=cost)))
        if unit_price is None:
            warnings.append("missing_price_evidence")
        return self._append(
            source_type="sale", source_id=source_id, actor=actor, occurred_at=occurred_at,
            postings=postings, warnings=warnings,
            metadata={"tender": tender_value.value, "quantity": str(quantity),
                      **({"unit_price": str(unit_price)} if unit_price is not None else {})},
        )

    def return_sale(
        self,
        *,
        source_id: str,
        original_sale_id: str | None,
        actor: str,
        occurred_at: datetime,
        refund: Decimal | int | str,
        tender: Tender | str,
        original_cogs: Decimal | int | str | None,
        quantity: int,
        resalable: bool,
    ) -> JournalEntry:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        tender_value = self._tender(tender)
        refund_amount = _money(refund)
        postings = [Posting(Account.SALES_REVENUE, debit=refund_amount), Posting(tender_value.account, credit=refund_amount)]
        warnings: list[str] = []
        if original_sale_id is None:
            warnings.append("unlinked_return_review_required")
        if original_cogs is None:
            warnings.append("missing_original_cost")
        elif resalable:
            cost = _money(original_cogs)
            postings.extend((Posting(Account.INVENTORY, debit=cost), Posting(Account.COGS, credit=cost)))
        else:
            cost = _money(original_cogs)
            postings.extend((Posting(Account.STOCK_LOSS, debit=cost), Posting(Account.INVENTORY, credit=cost)))
            warnings.append("damaged_return_stock_loss")
        return self._append(
            source_type="return", source_id=source_id, actor=actor, occurred_at=occurred_at,
            postings=postings, warnings=warnings,
            metadata={"tender": tender_value.value, "quantity": str(quantity),
                      "original_sale_id": original_sale_id or ""},
        )

    def expense(
        self,
        *,
        source_id: str,
        actor: str,
        occurred_at: datetime,
        amount: Decimal | int | str,
        tender: Tender | str | None,
        category: str,
        paid: bool,
    ) -> JournalEntry:
        if not category.strip():
            raise ValueError("expense category is required")
        value = _money(amount)
        warnings: list[str] = []
        if paid:
            if tender is None:
                raise ValueError("paid expense requires tender")
            tender_value = self._tender(tender)
            credit_account = tender_value.account
            metadata_tender = tender_value.value
        else:
            credit_account = Account.UNPAID_EXPENSE
            metadata_tender = "unpaid"
            warnings.append("expense_payment_state_incomplete")
        return self._append(
            source_type="expense", source_id=source_id, actor=actor, occurred_at=occurred_at,
            postings=(Posting(Account.OPERATING_EXPENSE, debit=value), Posting(credit_account, credit=value)),
            warnings=warnings, metadata={"category": category.strip(), "tender": metadata_tender},
        )

    def purchase(
        self,
        *,
        source_id: str,
        actor: str,
        occurred_at: datetime,
        amount: Decimal | int | str,
        tender: Tender | str | None,
        quantity: int,
        paid: bool,
    ) -> JournalEntry:
        """Record a stock receipt; inventory purchases are not operating expenses."""
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        value = _money(amount)
        warnings: list[str] = []
        if paid:
            if tender is None:
                raise ValueError("paid purchase requires tender")
            tender_value = self._tender(tender)
            credit_account = tender_value.account
            metadata_tender = tender_value.value
        else:
            credit_account = Account.UNPAID_EXPENSE
            metadata_tender = "unpaid"
            warnings.append("unpaid_supplier_amount")
        return self._append(
            source_type="purchase", source_id=source_id, actor=actor, occurred_at=occurred_at,
            postings=(Posting(Account.INVENTORY, debit=value), Posting(credit_account, credit=value)),
            warnings=warnings, metadata={"tender": metadata_tender, "quantity": str(quantity)},
        )

    def owner_injection(self, *, source_id: str, actor: str, occurred_at: datetime, amount: Decimal | int | str, tender: Tender | str) -> JournalEntry:
        tender_value = self._tender(tender)
        value = _money(amount)
        return self._append(source_type="owner_injection", source_id=source_id, actor=actor, occurred_at=occurred_at,
                            postings=(Posting(tender_value.account, debit=value), Posting(Account.OWNER_CAPITAL, credit=value)),
                            metadata={"tender": tender_value.value})

    def owner_drawing(self, *, source_id: str, actor: str, occurred_at: datetime, amount: Decimal | int | str, tender: Tender | str) -> JournalEntry:
        tender_value = self._tender(tender)
        value = _money(amount)
        return self._append(source_type="owner_drawing", source_id=source_id, actor=actor, occurred_at=occurred_at,
                            postings=(Posting(Account.OWNER_DRAWING, debit=value), Posting(tender_value.account, credit=value)),
                            metadata={"tender": tender_value.value})

    def opening_balance(self, *, source_id: str, actor: str, occurred_at: datetime, amount: Decimal | int | str, tender: Tender | str, source_known: bool) -> JournalEntry:
        tender_value = self._tender(tender)
        value = _money(amount)
        warnings = () if source_known else ("unknown_opening_balance_source",)
        return self._append(source_type="opening_balance", source_id=source_id, actor=actor, occurred_at=occurred_at,
                            postings=(Posting(tender_value.account, debit=value), Posting(Account.OPENING_BALANCE, credit=value)),
                            warnings=warnings, metadata={"tender": tender_value.value})

    def reverse(self, entry_id: str, *, source_id: str, actor: str, occurred_at: datetime) -> JournalEntry:
        original = next((entry for entry in self.entries if entry.entry_id == entry_id), None)
        if original is None:
            raise ValueError(f"entry not found: {entry_id}")
        postings = tuple(Posting(p.account, debit=p.credit, credit=p.debit) for p in original.postings)
        return self._append(source_type="reversal", source_id=source_id, actor=actor, occurred_at=occurred_at,
                            postings=postings, warnings=("reversal_of_original_entry",), reversal_of=entry_id,
                            metadata={"original_source_id": original.source_id})

    def close_day(
        self,
        *,
        business_date: date,
        timezone_name: str,
        actual_cash: Decimal | int | str | None,
        actual_bank: Decimal | int | str | None,
        explanations: Mapping[Tender, str] | None = None,
        locked_at: datetime | None = None,
    ) -> DailyClose:
        if business_date in self.closes:
            raise ValueError("daily close is already locked")
        zone = ZoneInfo(timezone_name)
        start = datetime.combine(business_date, time.min, tzinfo=zone).astimezone(timezone.utc)
        end = datetime.combine(business_date, time.max, tzinfo=zone).astimezone(timezone.utc)
        before = [entry for entry in self.entries if entry.occurred_at < start]
        during = [entry for entry in self.entries if start <= entry.occurred_at <= end]

        def tender_values(account: Account, source_types: set[str], *, credit: bool = False) -> dict[Tender, Decimal]:
            result = {}
            for tender, tender_account in ((Tender.CASH, Account.CASH), (Tender.BANK, Account.BANK)):
                result[tender] = sum(
                    ((p.credit if credit else p.debit) for e in during if e.source_type in source_types
                     for p in e.postings if p.account == tender_account), ZERO
                )
            return result

        opening = {t: sum((p.debit - p.credit for e in before for p in e.postings if p.account == t.account), ZERO) for t in Tender}
        sales = tender_values(Account.CASH, {"sale"})
        refunds = tender_values(Account.CASH, {"return"}, credit=True)
        expenses = tender_values(Account.CASH, {"expense"}, credit=True)
        purchases = tender_values(Account.CASH, {"purchase"}, credit=True)
        drawings = tender_values(Account.CASH, {"owner_drawing"}, credit=True)
        injections = tender_values(Account.CASH, {"owner_injection"})
        expected = {t: opening[t] + sales[t] - refunds[t] - expenses[t] - purchases[t] - drawings[t] + injections[t] for t in Tender}
        actual = {Tender.CASH: None if actual_cash is None else _money(actual_cash), Tender.BANK: None if actual_bank is None else _money(actual_bank)}
        variance = {t: None if actual[t] is None else actual[t] - expected[t] for t in Tender}
        warnings = []
        if actual_cash is None:
            warnings.append("missing_cash_count")
        if actual_bank is None:
            warnings.append("missing_bank_confirmation")
        for tender in Tender:
            if variance[tender] not in (None, ZERO) and not (explanations or {}).get(tender, "").strip():
                warnings.append(f"unexplained_{tender.value}_variance")
        close = DailyClose(
            shop_id=self.shop_id, business_date=business_date, timezone=timezone_name,
            opening=opening, sales=sales, refunds=refunds, expenses=expenses, purchases=purchases,
            owner_drawings=drawings, owner_injections=injections, expected=expected, actual=actual,
            variance=variance, warnings=tuple(sorted(warnings)), locked_at=_timestamp(locked_at),
        )
        self.closes[business_date] = close
        return close
