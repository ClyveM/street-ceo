"""Auditable stock movements and quantity-weighted average cost.

This module is deliberately storage- and transport-neutral.  A future API or
repository adapter can call ``InventoryBook`` inside its transaction boundary
and persist the returned movement records.  Quantities are whole base units;
pack quantities are converted before a movement is recorded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Dict, Optional


class InventoryError(ValueError):
    """Invalid inventory input or an operation that violates stock rules."""


class InsufficientStockError(InventoryError):
    """A movement would make sellable stock negative."""


class MovementType(str, Enum):
    RECEIPT = "receipt"
    SALE = "sale"
    RETURN = "return"
    ADJUSTMENT = "adjustment"
    STOCK_COUNT = "stock_count"


def _decimal(value: Decimal | int | str, field_name: str) -> Decimal:
    if isinstance(value, bool):
        raise InventoryError(f"{field_name} must be a decimal amount")
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise InventoryError(f"{field_name} must be a decimal amount") from None
    if not result.is_finite() or result < 0:
        raise InventoryError(f"{field_name} must be finite and non-negative")
    return result


def _positive_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InventoryError(f"{field_name} must be a positive whole number")
    return value


def _non_negative_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InventoryError(f"{field_name} must be a non-negative whole number")
    return value


@dataclass(frozen=True)
class PackQuantity:
    """A packaged quantity and its conversion to base units."""

    packs: int = 0
    units: int = 0
    units_per_pack: int = 1

    def __post_init__(self) -> None:
        _non_negative_int(self.packs, "packs")
        _non_negative_int(self.units, "units")
        _positive_int(self.units_per_pack, "units_per_pack")
        if self.base_units <= 0:
            raise InventoryError("quantity must contain at least one base unit")

    @property
    def base_units(self) -> int:
        return self.packs * self.units_per_pack + self.units


@dataclass
class ProductStock:
    product_id: str
    quantity: int = 0
    average_unit_cost: Decimal = Decimal("0")

    @property
    def inventory_value(self) -> Decimal:
        return self.average_unit_cost * self.quantity


@dataclass(frozen=True)
class Movement:
    movement_type: MovementType
    product_id: str
    quantity: int
    source_reference: str
    unit_cost: Decimal
    total_cost: Decimal
    quantity_before: int
    quantity_after: int
    average_unit_cost_after: Decimal
    actor: Optional[str] = None
    reason: Optional[str] = None
    related_source_reference: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class InventoryBook:
    """In-memory stock truth with append-only movement records.

    ``InventoryBook`` is intended to be used per shop/transaction aggregate;
    callers should persist the movement and stock snapshot atomically when
    integrating with a database.
    """

    def __init__(self) -> None:
        self._stock: Dict[str, ProductStock] = {}
        self._movements: list[Movement] = []

    def stock(self, product_id: str) -> ProductStock:
        self._require_product_id(product_id)
        current = self._current_stock(product_id)
        return ProductStock(current.product_id, current.quantity, current.average_unit_cost)

    def movements(self) -> tuple[Movement, ...]:
        return tuple(self._movements)

    def receive(
        self, product_id: str, quantity: PackQuantity, source_reference: str, *,
        unit_cost: Decimal | int | str, actor: Optional[str] = None,
    ) -> Movement:
        cost = _decimal(unit_cost, "unit_cost")
        return self._record(
            MovementType.RECEIPT, product_id, quantity.base_units, source_reference,
            cost, actor=actor,
        )

    def sell(
        self, product_id: str, quantity: PackQuantity, source_reference: str,
        *, actor: Optional[str] = None,
    ) -> Movement:
        return self._record(MovementType.SALE, product_id, -quantity.base_units,
                            source_reference, None, actor=actor)

    def return_stock(
        self, product_id: str, quantity: PackQuantity, source_reference: str,
        *, original_sale_reference: Optional[str] = None,
        original_unit_cost: Decimal | int | str | None = None,
        actor: Optional[str] = None,
        resalable: bool = True,
    ) -> Movement:
        if not resalable:
            raise InventoryError("non-resalable returns require a separate stock-loss adjustment")
        if original_unit_cost is None:
            raise InventoryError("resalable return requires original_unit_cost")
        cost = _decimal(original_unit_cost, "original_unit_cost")
        return self._record(
            MovementType.RETURN, product_id, quantity.base_units, source_reference,
            cost, actor=actor, related_source_reference=original_sale_reference,
        )

    def adjust(
        self, product_id: str, quantity: int, source_reference: str, *,
        reason: str, actor: str, unit_cost: Decimal | int | str | None = None,
    ) -> Movement:
        if quantity == 0:
            raise InventoryError("adjustment quantity cannot be zero")
        if not reason or not reason.strip() or not actor or not actor.strip():
            raise InventoryError("adjustment requires a reason and actor")
        cost = None if unit_cost is None else _decimal(unit_cost, "unit_cost")
        return self._record(MovementType.ADJUSTMENT, product_id, quantity, source_reference,
                            cost, actor=actor.strip(), reason=reason.strip())

    def stock_count(
        self, product_id: str, counted_quantity: int, source_reference: str, *,
        actor: str, unit_cost: Decimal | int | str | None = None,
    ) -> Movement:
        _non_negative_int(counted_quantity, "counted_quantity")
        if not actor or not actor.strip():
            raise InventoryError("stock count requires an actor")
        current = self._current_stock(product_id)
        delta = counted_quantity - current.quantity
        if delta == 0:
            raise InventoryError("stock count does not create a movement when unchanged")
        cost = None if unit_cost is None else _decimal(unit_cost, "unit_cost")
        return self._record(MovementType.STOCK_COUNT, product_id, delta, source_reference,
                            cost, actor=actor.strip(), reason="physical stock count")

    def _record(
        self, movement_type: MovementType, product_id: str, quantity: int,
        source_reference: str, unit_cost: Optional[Decimal], *, actor: Optional[str] = None,
        reason: Optional[str] = None, related_source_reference: Optional[str] = None,
    ) -> Movement:
        self._require_product_id(product_id)
        if not source_reference or not source_reference.strip():
            raise InventoryError("source_reference is required for every movement")
        if quantity == 0:
            raise InventoryError("movement quantity cannot be zero")
        current = self._current_stock(product_id)
        before = current.quantity
        if quantity < 0 and before + quantity < 0:
            raise InsufficientStockError(
                f"{product_id} has {before} base units; movement needs {-quantity}"
            )
        if quantity > 0 and before == 0 and unit_cost is None:
            raise InventoryError("positive movement requires unit_cost when stock has no cost")
        if quantity > 0 and unit_cost is None:
            unit_cost = current.average_unit_cost
        if unit_cost is None:
            unit_cost = current.average_unit_cost
        if quantity < 0:
            unit_cost = current.average_unit_cost

        after = before + quantity
        if quantity > 0:
            new_average = ((current.average_unit_cost * before) + (unit_cost * quantity)) / after
        else:
            new_average = current.average_unit_cost
        current.quantity = after
        current.average_unit_cost = new_average
        movement = Movement(
            movement_type, product_id, quantity, source_reference.strip(), unit_cost,
            unit_cost * abs(quantity), before, after, new_average, actor, reason,
            related_source_reference,
        )
        self._movements.append(movement)
        return movement

    @staticmethod
    def _require_product_id(product_id: str) -> None:
        if not isinstance(product_id, str) or not product_id.strip():
            raise InventoryError("product_id is required")

    def _current_stock(self, product_id: str) -> ProductStock:
        current = self._stock.get(product_id)
        if current is None:
            current = ProductStock(product_id)
            self._stock[product_id] = current
        return current
