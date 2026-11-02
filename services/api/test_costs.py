import io
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException

from services.api.app import InMemoryStore, ProductCreate, SaleCreate, SaleLine, ShopCreate, create_app
from services.api.costs import ExpenseCreate, InvoiceLineReview, InvoiceReviewRequest, ProductCostCorrectionCreate
from services.api.persistence import Settings
from services.ai.boundary import AIResult, InvoiceExtraction, InvoiceLineExtraction


def endpoint(app, path: str):
    return next(route.endpoint for route in app.routes if route.path == path)


class FakeUpload:
    def __init__(self, payload: bytes, filename: str, content_type: str) -> None:
        self.file = io.BytesIO(payload)
        self.filename = filename
        self.content_type = content_type

    async def read(self) -> bytes:
        return self.file.read()


class FakeInvoiceAI:
    def __init__(self, result):
        self.result = result
        self.requests = []

    def invoice_extract(self, request):
        self.requests.append(request)
        return self.result


def make_shop():
    app = create_app(InMemoryStore())
    shop = endpoint(app, "/shops")(ShopCreate(name="Cost shop"))
    record = app.state.store.shops[shop.id]
    product = endpoint(app, "/shops/{shop_id}/products")(
        ProductCreate(sku="COKE-300", name="Coca-Cola 300ml", unit_price_cents=150, opening_stock_qty=2), record
    )
    return app, record, product


def test_invoice_upload_review_and_confirmation_are_explicit_and_auditable() -> None:
    app, record, product = make_shop()
    upload = endpoint(app, "/api/v1/shops/{shop_id}/invoices")
    invoice = upload(record=record, invoice=FakeUpload(b"pdf-bytes", "supplier.pdf", "application/pdf"))

    assert invoice.extraction_status == "provider_unavailable"
    assert invoice.lines == []
    assert record.products[product.id].stock_qty == 2

    review = endpoint(app, "/api/v1/shops/{shop_id}/invoices/{invoice_id}/review")
    reviewed = review(
        invoice.id,
        InvoiceReviewRequest(lines=[InvoiceLineReview(
            description=product.name, sku=product.sku, product_id=product.id,
            quantity=10, line_total_cents=1000,
        )]),
        record,
    )
    assert reviewed.extraction_status == "needs_review"
    assert reviewed.lines[0].match_status == "accepted"
    assert reviewed.lines[0].calculated_unit_cost_micros == 1_000_000
    assert record.products[product.id].stock_qty == 2

    confirmed = endpoint(app, "/api/v1/shops/{shop_id}/invoices/{invoice_id}/confirm")(invoice.id, record)
    updated = record.products[product.id]
    assert confirmed.status == "confirmed"
    assert confirmed.stock_units_added == 10
    assert updated.stock_qty == 12
    assert updated.unit_cost_micros == 1_000_000
    assert len(record.cost_audits) == 1
    assert endpoint(app, "/api/v1/shops/{shop_id}/products/{product_id}/cost-history")(product.id, record)[0].invoice_id == invoice.id


def test_invoice_suggestion_cannot_silently_update_stock_or_cost() -> None:
    app, record, product = make_shop()
    invoice = endpoint(app, "/api/v1/shops/{shop_id}/invoices")(
        record=record, invoice=FakeUpload(b"image", "supplier.png", "image/png")
    )
    review = endpoint(app, "/api/v1/shops/{shop_id}/invoices/{invoice_id}/review")
    reviewed = review(
        invoice.id,
        InvoiceReviewRequest(lines=[InvoiceLineReview(
            description=product.name, sku=product.sku, quantity=1, line_total_cents=100,
        )]),
        record,
    )
    assert reviewed.lines[0].match_status == "suggested"
    with pytest.raises(HTTPException, match="explicit product match") as error:
        endpoint(app, "/api/v1/shops/{shop_id}/invoices/{invoice_id}/confirm")(invoice.id, record)
    assert error.value.status_code == 409
    assert record.products[product.id].stock_qty == 2
    assert record.products[product.id].unit_cost_micros is None


def test_invoice_upload_uses_review_only_adapter_and_does_not_receive_stock() -> None:
    extraction = InvoiceExtraction(
        status="review_required", provider="test", model="vision-test",
        lines=(InvoiceLineExtraction("Coca-Cola 300ml", "COKE-300", 2, 300, 150),),
        warnings=("check quantity",), review_only=True,
    )
    ai = FakeInvoiceAI(AIResult(extraction, "provider"))
    app = create_app(InMemoryStore(), invoice_ai=ai)
    shop = endpoint(app, "/shops")(ShopCreate(name="AI invoice shop"))
    record = app.state.store.shops[shop.id]
    product = endpoint(app, "/shops/{shop_id}/products")(
        ProductCreate(sku="COKE-300", name="Coca-Cola 300ml", unit_price_cents=150, opening_stock_qty=2), record
    )

    invoice = endpoint(app, "/api/v1/shops/{shop_id}/invoices")(
        record=record, invoice=FakeUpload(b"png-bytes", "supplier.png", "image/png")
    )

    assert invoice.extraction_status == "needs_review"
    assert invoice.extraction_source == "ocr_provider"
    assert invoice.lines[0].description == product.name
    assert invoice.lines[0].match_status == "unmatched"
    assert record.products[product.id].stock_qty == 2
    assert len(record.cost_audits) == 0
    assert ai.requests[0].catalogue[0].product_id == str(product.id)


def test_invoice_upload_preserves_provider_review_when_no_lines_are_legible() -> None:
    extraction = InvoiceExtraction(
        status="review_required", provider="test", model="vision-test",
        lines=(), warnings=("Invoice image is not legible. Human review required.",), review_only=True,
    )
    app = create_app(InMemoryStore(), invoice_ai=FakeInvoiceAI(AIResult(extraction, "provider")))
    shop = endpoint(app, "/shops")(ShopCreate(name="Unreadable invoice shop"))
    record = app.state.store.shops[shop.id]

    invoice = endpoint(app, "/api/v1/shops/{shop_id}/invoices")(
        record=record, invoice=FakeUpload(b"image", "supplier.png", "image/png")
    )

    assert invoice.extraction_status == "needs_review"
    assert invoice.extraction_source == "ocr_provider"
    assert invoice.lines == []
    assert invoice.warnings == ["Invoice image is not legible. Human review required."]


def test_invoice_adapter_failure_does_not_publish_partial_upload() -> None:
    class ExplodingAI:
        def invoice_extract(self, request):
            raise RuntimeError("provider down")

    app = create_app(InMemoryStore(), invoice_ai=ExplodingAI())
    shop = endpoint(app, "/shops")(ShopCreate(name="Atomic invoice shop"))
    record = app.state.store.shops[shop.id]
    with pytest.raises(RuntimeError, match="provider down"):
        endpoint(app, "/api/v1/shops/{shop_id}/invoices")(
            record=record, invoice=FakeUpload(b"image", "supplier.png", "image/png")
        )
    assert record.invoices == {}
    assert record.invoice_bytes == {}


def test_confirmed_expense_and_costed_sale_feed_profitability() -> None:
    app, record, product = make_shop()
    product.unit_cost_micros = 500_000
    sale = endpoint(app, "/shops/{shop_id}/sales")(
        SaleCreate(lines=[SaleLine(product_id=product.id, quantity=1)], tender="cash"), record, "sale-cost-1"
    )
    assert sale.cogs_micros == 500_000

    create_expense = endpoint(app, "/api/v1/shops/{shop_id}/expenses")
    expense = create_expense(ExpenseCreate(
        category="electricity", frequency="one_off", occurred_on=datetime.now(timezone.utc).date(), amount_cents=25, notes="Meter top-up"
    ), record)
    assert expense.status == "draft"
    muse = endpoint(app, "/api/v1/shops/{shop_id}/muse")
    draft_result = muse(type("Request", (), {"question": "What profit did I make today?"})(), record)
    assert draft_result.status == "answered"
    assert "USD 1.00" in draft_result.answer

    confirmed = endpoint(app, "/api/v1/shops/{shop_id}/expenses/{expense_id}/confirm")(expense.id, record)
    assert confirmed.status == "confirmed"
    result = muse(type("Request", (), {"question": "What profit did I make today?"})(), record)
    assert result.status == "answered"
    assert "Profit for today" in result.answer
    assert "USD 0.75" in result.answer


def test_direct_cost_correction_requires_confirmation_and_does_not_change_stock() -> None:
    app, record, product = make_shop()
    original_stock = product.stock_qty
    original_cost = product.unit_cost_micros
    create = endpoint(app, "/api/v1/shops/{shop_id}/products/{product_id}/cost-corrections")
    correction = create(product.id, ProductCostCorrectionCreate(
        unit_cost="0.42", effective_date=datetime.now(timezone.utc).date(),
        reason="Supplier price correction", source_ref="supplier-note-7", actor="owner",
    ), record)

    assert correction.status == "draft"
    assert correction.unit_cost_micros == 420_000
    assert record.products[product.id].stock_qty == original_stock
    assert record.products[product.id].unit_cost_micros == original_cost

    confirm = endpoint(app, "/api/v1/shops/{shop_id}/products/{product_id}/cost-corrections/{correction_id}/confirm")
    confirmed = confirm(product.id, correction.id, record)
    assert confirmed.status == "confirmed"
    assert record.products[product.id].stock_qty == original_stock
    assert record.products[product.id].unit_cost_micros == 420_000
    audit = endpoint(app, "/api/v1/shops/{shop_id}/products/{product_id}/cost-history")(product.id, record)[-1]
    assert audit.source_type == "direct_correction"
    assert audit.invoice_id is None
    assert audit.quantity_received == 0
    assert audit.stock_before == audit.stock_after == original_stock

    with pytest.raises(HTTPException, match="not a draft") as error:
        confirm(product.id, correction.id, record)
    assert error.value.status_code == 409


def test_direct_cost_correction_validates_decimal_and_shop_scope() -> None:
    app, record, product = make_shop()
    with pytest.raises(ValueError, match="decimal string"):
        ProductCostCorrectionCreate(
            unit_cost=0.42, effective_date=datetime.now(timezone.utc).date(),
            reason="Correction", source_ref="source", actor="owner",
        )
    with pytest.raises(ValueError, match="exactly one"):
        ProductCostCorrectionCreate(
            unit_cost="0.42", unit_cost_micros=420_000,
            effective_date=datetime.now(timezone.utc).date(), reason="Correction",
            source_ref="source", actor="owner",
        )
    with pytest.raises(HTTPException, match="product not found") as error:
        endpoint(app, "/api/v1/shops/{shop_id}/products/{product_id}/cost-corrections")(
            uuid4(), ProductCostCorrectionCreate(
                unit_cost_micros=420_000, effective_date=datetime.now(timezone.utc).date(),
                reason="Correction", source_ref="source", actor="owner",
            ), record
        )
    assert error.value.status_code == 404


def test_demo_reset_clears_financial_and_cost_records_and_sale_reports_stock_after() -> None:
    app = create_app(InMemoryStore())
    shop = endpoint(app, "/shops")(ShopCreate(name="Reset shop"))
    record = app.state.store.shops[shop.id]
    product = endpoint(app, "/shops/{shop_id}/products")(
        ProductCreate(sku="A", name="A", unit_price_cents=100, opening_stock_qty=3), record
    )
    sale = endpoint(app, "/shops/{shop_id}/sales")(
        SaleCreate(lines=[SaleLine(product_id=product.id, quantity=1)], tender="cash"), record, "reset-sale"
    )
    assert sale.stock_after[product.id] == 2

    demo_app = create_app(InMemoryStore(), Settings(demo_seed_enabled=True))
    previous_demo_record = next(iter(demo_app.state.store.shops.values()))
    previous_product = next(iter(previous_demo_record.products.values()))
    correction = endpoint(demo_app, "/api/v1/shops/{shop_id}/products/{product_id}/cost-corrections")(
        previous_product.id, ProductCostCorrectionCreate(
            unit_cost_micros=420_000, effective_date=datetime.now(timezone.utc).date(),
            reason="Synthetic pre-reset correction", source_ref="reset-fixture", actor="tester",
        ), previous_demo_record,
    )
    endpoint(demo_app, "/api/v1/shops/{shop_id}/products/{product_id}/cost-corrections/{correction_id}/confirm")(
        previous_product.id, correction.id, previous_demo_record,
    )
    previous_audit_ids = {audit.id for audit in previous_demo_record.cost_audits}
    assert any(audit.source_type == "direct_correction" for audit in previous_demo_record.cost_audits)
    demo_reset = endpoint(demo_app, "/api/v1/dev/demo/reset")()
    assert demo_reset.reset is True
    assert demo_reset.product_count == 6
    assert demo_reset.sales_count == 0
    assert demo_reset.invoice_count == 0
    assert demo_reset.expense_count == 0
    assert demo_reset.cost_audit_count == 6
    reset_record = demo_app.state.store.shops[demo_reset.shop_id]
    assert {audit.id for audit in reset_record.cost_audits}.isdisjoint(previous_audit_ids)
    assert len(reset_record.cost_audits) == 6
    assert all(audit.source_type == "demo_seed" and audit.source_ref == "STARTER-COGS-001" for audit in reset_record.cost_audits)
    assert all(audit.quantity_received == 0 and audit.stock_before == audit.stock_after and audit.invoice_id is None for audit in reset_record.cost_audits)
    assert reset_record.cost_corrections == {}
