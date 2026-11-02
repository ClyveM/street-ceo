"""Illustrative default-demo costs never rewrite user data or old sale COGS."""
import json
from copy import deepcopy
from pathlib import Path
from uuid import UUID, uuid4

from services.api.app import InMemoryStore, SaleCreate, SaleLine, create_app
from services.api.persistence import Settings


FIXTURE = json.loads(Path(__file__).with_name("demo_catalogue.json").read_text(encoding="utf-8"))
SHOP_ID = UUID(FIXTURE["shop"]["id"])


def test_fresh_memory_seed_has_approved_costs_and_illustrative_audit():
    store = InMemoryStore()
    store.seed_demo_shop()
    record = store.shops[SHOP_ID]
    assert len(record.cost_audits) == 6
    for starter in FIXTURE["products"]:
        product = record.products[UUID(starter["id"])]
        assert product.unit_cost_micros == starter["unit_cost_micros"]
        assert product.unit_price_cents == starter["unit_price_cents"]
        assert product.stock_qty == starter["stock_qty"]
        audit = next(item for item in record.cost_audits if item.product_id == product.id)
        assert audit.source_type == "demo_seed"
        assert audit.source_ref == "STARTER-COGS-001"
        assert audit.actor == "demo_seed"
        assert "Illustrative" in audit.reason
        assert audit.invoice_id is None
        assert audit.quantity_received == 0
        assert audit.stock_before == audit.stock_after == product.stock_qty
    saved = deepcopy(record)
    store.seed_demo_shop()
    assert record == saved
    coke = record.products[UUID(FIXTURE["products"][0]["id"])]
    sale = store.create_sale(record, SaleCreate(lines=[SaleLine(product_id=coke.id, quantity=2)], tender="cash"), "fresh", "fresh")
    assert sale.cogs_micros == 2_000_000


def test_sqlite_legacy_missing_only_upgrade_preserves_stock_prices_and_history(tmp_path):
    path = tmp_path / "starter.sqlite3"
    settings = Settings(store_backend="sqlite", sqlite_path=str(path), demo_seed_enabled=True)
    app = create_app(settings=settings, voice_catalogue_resolver=None)
    store = app.state.store
    ids = [UUID(item["id"]) for item in FIXTURE["products"]]
    with store.transaction():
        record = store.shops[SHOP_ID]
        # Reconstruct an old starter state without assumptions or their audits.
        record.cost_audits.clear()
        for product in record.products.values():
            product.unit_cost_micros = None
        unknown_request = SaleCreate(lines=[SaleLine(product_id=ids[0], quantity=1)], tender="cash")
        old_unknown = store.create_sale(record, unknown_request, "old-unknown", "old-unknown")
        record.products[ids[1]].unit_cost_micros = 0
        old_zero = store.create_sale(record, SaleCreate(lines=[SaleLine(product_id=ids[1], quantity=1)], tender="cash"), "old-zero", "old-zero")
        record.products[ids[2]].unit_price_cents = 999
        record.products[ids[3]].unit_cost_micros = 900001
        record.products[ids[4]].name = "User renamed chips"
        record.products[ids[5]].sku = "USER-SOAP"
        old_receipts = {key: (fingerprint, sale.model_dump(mode="json")) for key, (fingerprint, sale) in record.idempotent_sales.items()}
        old_stock_prices = {key: (product.stock_qty, product.unit_price_cents) for key, product in record.products.items()}
    assert old_unknown.cogs_micros is None
    assert old_zero.cogs_micros == 0
    store.close()

    app = create_app(settings=settings, voice_catalogue_resolver=None)
    store = app.state.store
    record = store.shops[SHOP_ID]
    assert {key: (product.stock_qty, product.unit_price_cents) for key, product in record.products.items()} == old_stock_prices
    assert {key: (fingerprint, sale.model_dump(mode="json")) for key, (fingerprint, sale) in record.idempotent_sales.items()} == old_receipts
    assert record.products[ids[0]].unit_cost_micros == 1_000_000
    assert record.products[ids[1]].unit_cost_micros == 0
    assert record.products[ids[2]].unit_cost_micros == 1_800_000
    assert record.products[ids[3]].unit_cost_micros == 900001
    assert record.products[ids[4]].unit_cost_micros is None
    assert record.products[ids[5]].unit_cost_micros is None
    assert {audit.product_id for audit in record.cost_audits} == {ids[0], ids[2]}
    with store.transaction():
        record = store.shops[SHOP_ID]
        assert store.create_sale(record, unknown_request, "old-unknown", "old-unknown").cogs_micros is None
        future = store.create_sale(record, unknown_request, "future", "future")
        assert future.cogs_micros == 1_000_000
    store.close()
    app = create_app(settings=settings, voice_catalogue_resolver=None)
    assert len(app.state.store.shops[SHOP_ID].cost_audits) == 2
    assert app.state.store.shops[SHOP_ID].idempotent_sales["old-unknown"][1].cogs_micros is None
    app.state.store.close()


def test_backfill_skips_invoice_or_existing_audit_and_non_demo_identity():
    store = InMemoryStore()
    store.seed_demo_shop()
    record = store.shops[SHOP_ID]
    products = list(record.products.values())
    products[0].unit_cost_micros = None
    products[0].cost_source_invoice_id = uuid4()
    products[1].unit_cost_micros = None  # Existing audit means do not undo an intentional unknown.
    before = deepcopy(record)
    store.seed_demo_shop()
    assert record == before
    record.cost_audits.clear()
    record.shop.name = "Owner renamed shop"
    before = deepcopy(record)
    store.seed_demo_shop()
    assert record == before
