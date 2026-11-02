"""Bundled starter pictures survive clean setup and never replace shop uploads."""
import base64
import asyncio
from copy import deepcopy
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from uuid import UUID

import httpx
from PIL import Image
import pytest

from services.api.app import InMemoryStore, SaleCreate, SaleLine, create_app
from services.api.persistence import Settings

STARTER = json.loads((Path(__file__).resolve().parents[1] / "services/api/demo_catalogue.json").read_text())
SHOP = UUID(STARTER["shop"]["id"])
BASE = f"/api/v1/shops/{SHOP}"
HEADERS = {"X-Shop-ID": str(SHOP)}
CUSTOM_PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aH1cAAAAASUVORK5CYII=")


class Client:
    """Use the project's direct ASGI pattern; no sockets or live server."""
    def __init__(self, app):
        self.app = app

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def request(self, method, path, **kwargs):
        async def run():
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test") as client:
                return await client.request(method, path, **kwargs)
        return asyncio.run(run())

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)


def build(tmp_path, backend="sqlite", seed=True):
    return create_app(settings=Settings(store_backend=backend, sqlite_path=str(tmp_path / "pictures.sqlite3"),
                                      demo_seed_enabled=seed), voice_catalogue_resolver=None)


def close(app):
    if hasattr(app.state.store, "close"):
        app.state.store.close()


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
def test_clean_seed_exposes_six_real_local_images(tmp_path, backend):
    app = build(tmp_path, backend)
    try:
        with Client(app) as client:
            listing = client.get(BASE + "/product-images", headers=HEADERS)
            assert listing.status_code == 200
            items = listing.json()
            assert {x["product_id"] for x in items} == {x["id"] for x in STARTER["products"]}
            assert len(items) == 6
            hashes = set()
            for item in items:
                endpoint = BASE + f'/products/{item["product_id"]}/image'
                assert client.get(endpoint, headers=HEADERS).json() == item
                response = client.get(endpoint + "/content", headers=HEADERS)
                assert response.status_code == 200
                assert response.headers["content-type"] == "image/png"
                assert response.headers["cache-control"] == "private, no-store"
                assert response.headers["x-content-type-options"] == "nosniff"
                assert response.headers["etag"] == '"' + item["sha256"] + '"'
                assert len(response.content) == item["size_bytes"]
                assert sha256(response.content).hexdigest() == item["sha256"]
                with Image.open(BytesIO(response.content)) as image:
                    assert image.format == "PNG"
                    assert min(image.size) >= 128
                    image.verify()
                hashes.add(item["sha256"])
                asset = Path(__file__).resolve().parents[1] / "services/api/demo_product_images" / item["filename"]
                assert asset.read_bytes() == response.content
                assert asset.with_suffix(".svg").is_file()
                assert client.get(endpoint + "/content", headers={"X-Shop-ID": str(UUID(int=999))}).status_code in (403, 404)
            assert len(hashes) == 6
            record = app.state.store.shops[SHOP]
            saved = deepcopy(record)
            app.state.store.seed_demo_shop()
            assert record == saved
    finally:
        close(app)


def test_missing_only_sqlite_backfill_keeps_upload_and_financial_state(tmp_path):
    app = build(tmp_path)
    product_id = UUID(STARTER["products"][0]["id"])
    with Client(app) as client:
        uploaded = client.post(BASE + f"/products/{product_id}/image", headers=HEADERS,
                               files={"image": ("my-cola.png", CUSTOM_PNG, "image/png")})
        assert uploaded.status_code == 201, uploaded.text
        upload = uploaded.json()
    with app.state.store.transaction():
        record = app.state.store.shops[SHOP]
        record.product_images = {UUID(upload["id"]): record.product_images[UUID(upload["id"]) ]}
        record.product_image_bytes = {UUID(upload["id"]): CUSTOM_PNG}
        app.state.store.create_sale(record, SaleCreate(lines=[SaleLine(product_id=product_id, quantity=1)], tender="cash"), "fixture", "fixture")
        record.products[product_id].unit_price_cents = 987
        record.products[product_id].unit_cost_micros = 456789
        before = deepcopy(record)
    close(app)
    app = build(tmp_path)
    try:
        after = deepcopy(app.state.store.shops[SHOP])
        assert len(after.product_images) == 6
        assert after.product_images[UUID(upload["id"])].model_dump(mode="json") == upload
        assert after.product_image_bytes[UUID(upload["id"])] == CUSTOM_PNG
        after.product_images = before.product_images
        after.product_image_bytes = before.product_image_bytes
        assert after == before  # Includes receipts, cost audits, prices and decremented stock.
        with Client(app) as client:
            assert client.get(BASE + f"/products/{product_id}/image", headers=HEADERS).json() == upload
            assert client.get(BASE + f"/products/{product_id}/image/content", headers=HEADERS).content == CUSTOM_PNG
        saved = deepcopy(app.state.store.shops[SHOP])
        close(app)
        app = build(tmp_path)
        assert app.state.store.shops[SHOP] == saved
    finally:
        close(app)


@pytest.mark.parametrize("change", ["name", "sku", "deleted", "shop"])
def test_existing_non_starter_identity_never_gets_assumed_picture(change):
    store = InMemoryStore()
    store.seed_demo_shop()
    record = store.shops[SHOP]
    record.product_images.clear()
    record.product_image_bytes.clear()
    product_id = UUID(STARTER["products"][0]["id"])
    if change == "shop":
        record.shop.name = "My different shop"
    elif change == "deleted":
        del record.products[product_id]
    else:
        setattr(record.products[product_id], change, "Owner replacement")
    products = deepcopy(record.products)
    store.seed_demo_shop()
    assert record.products == products
    if change == "shop":
        assert record.product_images == {}
    else:
        assert len(record.product_images) == 5
        assert product_id not in {x.product_id for x in record.product_images.values()}


def test_explicit_disabled_seed_has_no_demo_pictures(tmp_path):
    app = build(tmp_path, seed=False)
    try:
        assert app.state.store.shops == {}
    finally:
        close(app)
