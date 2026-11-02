"""Review-only OCR contract; synthetic images and injected HTTP, never real cloud."""
import base64
from dataclasses import asdict
from hashlib import sha256
from io import BytesIO
import json
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image
import pytest

from services.ai.handwritten_sales import (
    MetaHandwrittenSalesProvider, extract_handwritten_sales, validate_image,
)
from services.ai.tracing import SQLiteTraceStore, trace_context

CATALOGUE = [{"product_id": "bread", "name": "Bread loaf", "sku": "BREAD"}]


def image(fmt="PNG"):
    stream = BytesIO()
    Image.new("RGB", (12, 12), "white").save(stream, format=fmt)
    return stream.getvalue()


def line(**kwargs):
    return {"raw_label": "bread", "product_id": "bread", "quantity": 2,
            "unit_price_cents": 180, "line_total_cents": 360, **kwargs}


class Provider:
    model = "fake-vision"
    def __init__(self, rows=None):
        self.rows = [line()] if rows is None else rows
        self.calls = []
    def extract(self, *args):
        self.calls.append(args)
        return {"lines": self.rows, "warnings": []}


def test_review_only_known_and_unknown_preserved_never_prices_from_catalogue():
    provider = Provider([line(), line(raw_label="unclear", product_id=None, quantity=None,
                                      unit_price_cents=None, line_total_cents=None)])
    data = image()
    result = extract_handwritten_sales(data, "image/png", CATALOGUE, provider=provider)
    assert result.status == "review" and result.provider_called
    assert result.image_sha256 == sha256(data).hexdigest()
    assert result.lines[0].quantity == 2
    assert result.lines[1].quantity is None and result.lines[1].product_id is None
    assert result.lines[1].line_total_cents is None
    assert result.warnings and not hasattr(result, "tender")
    assert len(provider.calls) == 1
    assert set(asdict(result.lines[0])) == set(line())


@pytest.mark.parametrize("override", [
    {"product_id": "invented"}, {"quantity": True}, {"quantity": 0}, {"quantity": "2"},
    {"unit_price_cents": 1.8}, {"line_total_cents": -1}, {"line_total_cents": 359},
    {"raw_label": ""}, {"cash": 360},
], ids=["unknown-id", "bool-qty", "zero-qty", "string-qty", "decimal-price", "negative-total", "bad-math", "empty-label", "extra-field"])
def test_bad_provider_output_fails_whole_draft(override):
    result = extract_handwritten_sales(image(), "image/png", CATALOGUE,
        provider=Provider([line(), line(**override)]))
    assert result.status == "unavailable" and result.lines == ()
    assert result.reason == "invalid_response"


@pytest.mark.parametrize("fmt,mime", [("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")])
def test_supported_images_are_decoded(fmt, mime):
    assert len(validate_image(image(fmt), mime)) == 64


@pytest.mark.parametrize("data,mime", [
    (b"", "image/png"), (b"bad image", "image/png"), (b"%PDF-1.0", "application/pdf"),
    (image(), "image/jpeg"), (b"x" * (5 * 1024 * 1024 + 1), "image/png"),
    (image()[:30], "image/png"),
], ids=["empty", "invalid", "pdf", "mime-mismatch", "oversize", "truncated"])
def test_invalid_upload_never_calls_provider(data, mime):
    provider = Provider()
    with pytest.raises(ValueError):
        extract_handwritten_sales(data, mime, CATALOGUE, provider=provider)
    assert provider.calls == []


def test_large_pixel_image_and_multiframe_rejected():
    out = BytesIO()
    Image.new("1", (4001, 4000)).save(out, format="PNG")
    with pytest.raises(ValueError):
        validate_image(out.getvalue(), "image/png")
    out = BytesIO()
    Image.new("RGB", (12, 12), "red").save(out, format="PNG", save_all=True,
        append_images=[Image.new("RGB", (12, 12), "blue")])
    with pytest.raises(ValueError):
        validate_image(out.getvalue(), "image/png")


def test_missing_explicit_vision_config_has_no_fake_ocr(monkeypatch):
    from services.ai import handwritten_sales as module
    with patch.object(module.InvoiceVisionSettings, "from_env", return_value=module.InvoiceVisionSettings("", None)):
        result = extract_handwritten_sales(image(), "image/png", CATALOGUE)
    assert result.reason == "provider_not_configured" and not result.provider_called
    assert result.lines == () and result.source == "none"


def test_empty_read_preserves_review_warning_not_fake_items():
    result = extract_handwritten_sales(image(), "image/png", CATALOGUE, provider=Provider([]))
    assert result.status == "review" and result.lines == () and result.warnings


def test_real_adapter_shape_and_trace_omits_binary_and_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("STREET_CEO_TRACE_DATABASE", str(tmp_path / "trace.sqlite3"))
    monkeypatch.setenv("STREET_CEO_CONSOLE_TRACE", "off")
    sent = []
    def post(url, **kwargs):
        sent.append((url, kwargs))
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {
            "choices": [{"message": {"content": json.dumps({"lines": [line()], "warnings": []})}}]})
    provider = MetaHandwrittenSalesProvider("private-key", "synthetic-vision", SimpleNamespace(post=post))
    data = image()
    with trace_context("paper-test", shop_id="test-shop"):
        result = extract_handwritten_sales(data, "image/png", CATALOGUE, provider=provider)
    assert result.status == "review"
    request = sent[0][1]["json"]
    assert request["model"] == "synthetic-vision"
    assert request["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    prompt = request["messages"][0]["content"]
    assert '"product_id":"bread"' in prompt and "never guess" in prompt
    logs = json.dumps(SQLiteTraceStore(tmp_path / "trace.sqlite3").read("paper-test"))
    assert "private-key" not in logs and base64.b64encode(data).decode() not in logs
    assert "binary image" in logs and "handwritten_daily_sales" in logs


def test_busy_pool_no_extra_call_and_no_retry():
    from services.ai import handwritten_sales as module
    provider = Provider()
    with patch.object(module, "_CAPACITY") as capacity, patch.object(module._POOL, "submit") as submit:
        capacity.acquire.return_value = False
        result = extract_handwritten_sales(image(), "image/png", CATALOGUE, provider=provider)
    assert result.reason == "provider_busy" and not result.provider_called
    submit.assert_not_called()


def test_timeout_is_bounded_and_nonactionable():
    from concurrent.futures import TimeoutError
    from services.ai import handwritten_sales as module
    class Future:
        def add_done_callback(self, callback): callback(self)
        def result(self, timeout):
            assert timeout == 24.0
            raise TimeoutError()
        def cancel(self): return False
    with patch.object(module._POOL, "submit", return_value=Future()) as submit:
        result = extract_handwritten_sales(image(), "image/png", CATALOGUE, provider=Provider())
    assert result.reason == "timeout" and result.lines == () and result.provider_called
    assert submit.call_count == 1
