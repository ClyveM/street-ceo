from decimal import Decimal

import pytest

from services.inventory import InventoryBook, InsufficientStockError, InventoryError, PackQuantity, MovementType


def q(packs=0, units=0, per_pack=1):
    return PackQuantity(packs, units, per_pack)


def test_receipt_converts_packs_and_uses_quantity_weighted_average_cost():
    book = InventoryBook()
    first = book.receive("sugar", q(packs=2, per_pack=24), "purchase:PO-1", unit_cost="1.20")
    second = book.receive("sugar", q(units=12), "purchase:PO-2", unit_cost="1.80")

    assert first.quantity == 48
    assert book.stock("sugar").quantity == 60
    assert book.stock("sugar").average_unit_cost == Decimal("1.32")
    assert second.total_cost == Decimal("21.60")


def test_sale_uses_pre_sale_wac_and_never_creates_negative_stock():
    book = InventoryBook()
    book.receive("oil", q(units=10), "purchase:PO-1", unit_cost="2.00")
    sale = book.sell("oil", q(units=3), "sale:S-1")

    assert sale.movement_type is MovementType.SALE
    assert sale.unit_cost == Decimal("2.00")
    assert sale.total_cost == Decimal("6.00")
    assert book.stock("oil").quantity == 7
    with pytest.raises(InsufficientStockError):
        book.sell("oil", q(units=8), "sale:S-2")
    assert book.stock("oil").quantity == 7


def test_resalable_return_restock_uses_original_sale_cost_and_source_link():
    book = InventoryBook()
    book.receive("bread", q(units=5), "purchase:PO-1", unit_cost="1.00")
    sale = book.sell("bread", q(units=2), "sale:S-1")
    returned = book.return_stock(
        "bread", q(units=1), "return:R-1", original_sale_reference="sale:S-1",
        original_unit_cost=sale.unit_cost,
    )

    assert returned.movement_type is MovementType.RETURN
    assert returned.related_source_reference == "sale:S-1"
    assert returned.unit_cost == Decimal("1.00")
    assert book.stock("bread").quantity == 4


def test_adjustment_and_count_require_audit_data_and_reconcile_delta():
    book = InventoryBook()
    book.receive("soap", q(units=10), "purchase:PO-1", unit_cost="0.50")
    with pytest.raises(InventoryError):
        book.adjust("soap", -1, "adjustment:A-1", reason="", actor="owner")
    adjustment = book.adjust("soap", -2, "adjustment:A-1", reason="damaged", actor="owner")
    count = book.stock_count("soap", 12, "count:C-1", actor="owner", unit_cost="0.60")

    assert adjustment.quantity == -2
    assert count.movement_type is MovementType.STOCK_COUNT
    assert count.quantity == 4
    assert book.stock("soap").quantity == 12


def test_every_movement_requires_source_and_return_requires_cost():
    book = InventoryBook()
    with pytest.raises(InventoryError):
        book.receive("rice", q(units=1), "", unit_cost="1")
    book.receive("rice", q(units=2), "purchase:PO-1", unit_cost="1")
    with pytest.raises(InventoryError):
        book.return_stock("rice", q(units=1), "return:R-1")
