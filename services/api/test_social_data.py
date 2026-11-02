import io
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from services.ai.boundary import StructuredAI
from services.api.app import InMemoryStore, ProductCreate, ShopCreate, create_app
from services.api.social_data import ShopImageMetadata, SocialBriefRequest, SocialDraftRequest, SocialImageGenerationRequest


def endpoint(app, path: str):
    return next(route.endpoint for route in app.routes if route.path == path)


class FakeUpload:
    def __init__(self, payload: bytes, filename: str, content_type: str) -> None:
        self.file = io.BytesIO(payload)
        self.filename = filename
        self.content_type = content_type


def test_social_brief_returns_selected_shop_products_and_image_metadata() -> None:
    app = create_app(InMemoryStore(), social_ai=StructuredAI(None), image_ai=StructuredAI(None))
    shop = endpoint(app, "/shops")(ShopCreate(name="Social shop"))
    record = app.state.store.shops[shop.id]
    product = endpoint(app, "/shops/{shop_id}/products")(
        ProductCreate(sku="COKE-300", name="Coca-Cola 300ml", unit_price_cents=150, opening_stock_qty=18), record
    )
    request = SocialBriefRequest(
        product_ids=[product.id],
        shop_image=ShopImageMetadata(filename="front.jpg", content_type="image/jpeg", size_bytes=2048, width=1200, height=800),
    )

    result = endpoint(app, "/api/v1/shops/{shop_id}/social/brief")(request, record)

    assert result.shop_id == shop.id
    assert result.catalogue_source == "repository"
    assert result.products[0].name == "Coca-Cola 300ml"
    assert result.products[0].stock_qty == 18
    assert result.shop_image is not None
    assert result.shop_image.filename == "front.jpg"
    assert result.created_at.tzinfo == timezone.utc


def test_social_brief_rejects_unknown_product_without_fabricating_data() -> None:
    app = create_app(InMemoryStore(), social_ai=StructuredAI(None), image_ai=StructuredAI(None))
    shop = endpoint(app, "/shops")(ShopCreate(name="Social shop"))
    record = app.state.store.shops[shop.id]

    with pytest.raises(HTTPException, match="selected product not found") as error:
        endpoint(app, "/api/v1/shops/{shop_id}/social/brief")(
            SocialBriefRequest(product_ids=[uuid4()]), record
        )
    assert error.value.status_code == 404


def test_social_image_metadata_requires_image_mime_type_and_bounded_size() -> None:
    with pytest.raises(ValueError, match="image MIME"):
        ShopImageMetadata(filename="shop.txt", content_type="text/plain", size_bytes=20)
    with pytest.raises(ValueError):
        ShopImageMetadata(filename="shop.jpg", content_type="image/jpeg", size_bytes=10 * 1024 * 1024 + 1)


def test_product_image_upload_is_shop_scoped_and_generation_reports_provider_blocker() -> None:
    app = create_app(InMemoryStore(), social_ai=StructuredAI(None), image_ai=StructuredAI(None))
    shop = endpoint(app, "/shops")(ShopCreate(name="Image shop"))
    record = app.state.store.shops[shop.id]
    product = endpoint(app, "/shops/{shop_id}/products")(
        ProductCreate(sku="COKE-300", name="Coca-Cola 300ml", unit_price_cents=150, opening_stock_qty=18), record
    )
    upload = FakeUpload(b"small-image-bytes", "front.png", "image/png")
    upload_route = endpoint(app, "/api/v1/shops/{shop_id}/products/{product_id}/image")
    metadata = upload_route(product.id, record, upload)

    assert metadata.shop_id == shop.id
    assert metadata.product_id == product.id
    assert metadata.storage_backend == "memory"
    assert metadata.storage_ref.startswith("memory://product-images/")
    assert metadata.size_bytes == len(b"small-image-bytes")
    assert len(metadata.sha256) == 64
    get_image_route = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/products/{product_id}/image" and "GET" in route.methods)
    assert get_image_route(product.id, record) == metadata

    generation = endpoint(app, "/api/v1/shops/{shop_id}/social/image-generation")(
        SocialImageGenerationRequest(product_ids=[product.id], source_image_id=metadata.id, brief="Create a bright product post."), record
    )
    assert generation.status == "provider_not_configured"
    assert generation.provider == "none"
    assert generation.output_url is None
    assert generation.draft_only is True
    assert any("MUSE_IMAGE_MODEL" in warning for warning in generation.warnings)


def test_product_image_upload_rejects_unsafe_filename_and_unknown_product() -> None:
    app = create_app(InMemoryStore(), social_ai=StructuredAI(None), image_ai=StructuredAI(None))
    shop = endpoint(app, "/shops")(ShopCreate(name="Image shop"))
    record = app.state.store.shops[shop.id]
    upload_route = endpoint(app, "/api/v1/shops/{shop_id}/products/{product_id}/image")
    unsafe = FakeUpload(b"x", "../shop.png", "image/png")

    with pytest.raises(HTTPException, match="product not found") as error:
        upload_route(uuid4(), record, unsafe)
    assert error.value.status_code == 404

    product = endpoint(app, "/shops/{shop_id}/products")(ProductCreate(sku="A", name="A", unit_price_cents=10), record)
    unsafe = FakeUpload(b"x", "../shop.png", "image/png")
    with pytest.raises(HTTPException, match="safe image basename") as error:
        upload_route(product.id, record, unsafe)
    assert error.value.status_code == 422


def test_social_draft_and_image_generation_are_shop_scoped_and_retrievable() -> None:
    app = create_app(InMemoryStore(), social_ai=StructuredAI(None), image_ai=StructuredAI(None))
    shop = endpoint(app, "/shops")(ShopCreate(name="Social shop"))
    other_shop = endpoint(app, "/shops")(ShopCreate(name="Other shop"))
    record = app.state.store.shops[shop.id]
    other_record = app.state.store.shops[other_shop.id]
    product = endpoint(app, "/shops/{shop_id}/products")(
        ProductCreate(sku="COKE-300", name="Coca-Cola 300ml", unit_price_cents=150, opening_stock_qty=18), record
    )
    other_product = endpoint(app, "/shops/{shop_id}/products")(
        ProductCreate(sku="OTHER", name="Other product", unit_price_cents=200), other_record
    )

    draft_route = endpoint(app, "/api/v1/shops/{shop_id}/social/draft")
    draft = draft_route(
        SocialDraftRequest(product_ids=[product.id], brief="Make a bright shop announcement."), record
    )
    assert draft.shop_id == shop.id
    assert draft.draft_only is True
    assert draft.status == "unavailable"
    assert draft.selected_product_ids == []

    image_route = endpoint(app, "/api/v1/shops/{shop_id}/social/image-generation")
    generation = image_route(
        SocialImageGenerationRequest(product_ids=[product.id], brief="Create a bright product post."), record
    )
    get_generation = next(
        route.endpoint for route in app.routes
        if route.path == "/api/v1/shops/{shop_id}/social/image-generation/{generation_id}"
        and "GET" in route.methods
    )
    assert get_generation(generation.id, record) == generation

    with pytest.raises(HTTPException, match="selected product not found") as error:
        draft_route(SocialDraftRequest(product_ids=[other_product.id], brief="Cross-shop attempt."), record)
    assert error.value.status_code == 404
