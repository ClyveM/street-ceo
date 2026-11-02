"""Independent starter-cost gate: pure stores and temporary SQLite files only."""
from copy import deepcopy
from uuid import UUID, uuid4

import pytest

from services.api.app import InMemoryStore, SaleCreate, SaleLine, create_app
from services.api.persistence import Settings
from services.api.sqlite_store import SQLiteStore

SHOP = UUID("00000000-0000-0000-0000-000000000001")
PRODUCT = SHOP


@pytest.mark.parametrize("field,value", [
    ("name", "Custom shop"), ("currency", "ZAR"), ("timezone", "Africa/Johannesburg"),
])
def test_shop_identity_change_blocks_all_backfill(field, value):
    store = InMemoryStore()
    store.seed_demo_shop()
    record = store.shops[SHOP]
    record.cost_audits.clear()
    for product in record.products.values():
        product.unit_cost_micros = None
    setattr(record.shop, field, value)
    before = deepcopy(record)
    store.seed_demo_shop()
    assert record == before


@pytest.mark.parametrize("change", ["deleted", "id", "shop_id", "sku", "name"])
def test_changed_or_deleted_product_is_never_recreated_or_costed(change):
    store = InMemoryStore()
    store.seed_demo_shop()
    record = store.shops[SHOP]
    record.cost_audits.clear()
    product = record.products[PRODUCT]
    product.unit_cost_micros = None
    if change == "deleted":
        del record.products[PRODUCT]
    elif change == "id":
        del record.products[PRODUCT]
        product.id = uuid4()
        record.products[product.id] = product
    else:
        setattr(product, change, uuid4() if change == "shop_id" else "custom")
    before = deepcopy(record)
    store.seed_demo_shop()
    assert record == before


def test_startup_save_fault_rolls_back_costs_and_audits_then_reopens(tmp_path, monkeypatch):
    path = str(tmp_path / "legacy.sqlite3")
    store = SQLiteStore(path)
    with store.transaction():
        store.seed_demo_shop()
        record = store.shops[SHOP]
        record.cost_audits.clear()
        for product in record.products.values():
            product.unit_cost_micros = None
    before = deepcopy(store.shops)
    store.close()
    original_save = SQLiteStore._save

    def fail_after_writing(self):
        original_save(self)
        raise RuntimeError("synthetic startup persistence failure")

    settings = Settings(store_backend="sqlite", sqlite_path=path, demo_seed_enabled=True)
    with monkeypatch.context() as patch:
        patch.setattr(SQLiteStore, "_save", fail_after_writing)
        with pytest.raises(RuntimeError, match="synthetic startup"):
            create_app(settings=settings, voice_catalogue_resolver=None)
    reopened = SQLiteStore(path)
    assert reopened.shops == before
    reopened.close()
    app = create_app(settings=settings, voice_catalogue_resolver=None)
    assert len(app.state.store.shops[SHOP].cost_audits) == 6
    app.state.store.close()


def test_receipt_snapshot_and_retry_survive_later_cost_changes(tmp_path):
    store = SQLiteStore(str(tmp_path / "receipts.sqlite3"))
    payload = SaleCreate(lines=[SaleLine(product_id=PRODUCT, quantity=2)], tender="cash")
    with store.transaction():
        store.seed_demo_shop()
        record = store.shops[SHOP]
        receipt = store.create_sale(record, payload, "first", "fingerprint")
        saved = receipt.model_dump(mode="json")
        assert receipt.cogs_micros == 2_000_000
        record.products[PRODUCT].unit_cost_micros = 0
    path = str(store.path)
    store.close()
    store = SQLiteStore(path)
    with store.transaction():
        record = store.shops[SHOP]
        store.seed_demo_shop()
        before_stock = record.products[PRODUCT].stock_qty
        assert store.create_sale(record, payload, "first", "fingerprint").model_dump(mode="json") == saved
        assert record.products[PRODUCT].stock_qty == before_stock
        assert store.create_sale(record, payload, "second", "second").cogs_micros == 0
    store.close()
