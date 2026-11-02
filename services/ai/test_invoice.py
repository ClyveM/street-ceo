import json

try:
    from services.ai.boundary import InvoiceCatalogueProduct, InvoiceImageRequest, StructuredAI
    from services.ai.invoice import META_CHAT_ENDPOINT, MetaInvoiceVisionProvider, InvoiceVisionSettings, build_invoice_vision_ai
except ModuleNotFoundError:  # unittest/pytest discovery from services/ai
    from boundary import InvoiceCatalogueProduct, InvoiceImageRequest, StructuredAI
    from invoice import META_CHAT_ENDPOINT, MetaInvoiceVisionProvider, InvoiceVisionSettings, build_invoice_vision_ai


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class Http:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return Response(self.payload)


def image_request():
    return InvoiceImageRequest("data:image/png;base64,AAAA", "image/png", "supplier.png")


def provider_payload():
    return {"choices": [{"message": {"content": json.dumps({
        "status": "review_required", "provider": "ignored", "model": "ignored",
        "lines": [{"description": "Coca-Cola 300ml", "sku": "COKE-300", "quantity": 2, "line_total_minor": 300, "unit_cost_minor": 150}],
        "warnings": [], "review_only": True,
    })}}]}


def test_invoice_provider_sends_user_image_and_structured_review_prompt():
    http = Http(provider_payload())
    provider = MetaInvoiceVisionProvider("secret", "verified-vision-model", http)
    result = StructuredAI(None, invoice_provider=provider).invoice_extract(image_request())
    assert result.source == "provider"
    assert result.value.status == "review_required"
    assert result.value.review_only is True
    assert result.value.lines[0].quantity == 2
    call = http.calls[0]
    assert call[0][0] == META_CHAT_ENDPOINT
    assert call[1]["json"]["model"] == "verified-vision-model"
    assert call[1]["json"]["messages"][0]["content"][1]["type"] == "image_url"
    assert call[1]["json"]["response_format"] == {"type": "json_object"}


def test_invoice_provider_uses_file_content_part_for_pdf():
    http = Http(provider_payload())
    provider = MetaInvoiceVisionProvider("secret", "muse-spark-1.3", http)
    result = StructuredAI(None, invoice_provider=provider).invoice_extract(
        InvoiceImageRequest("data:application/pdf;base64,AAAA", "application/pdf", "supplier.pdf")
    )
    assert result.source == "provider"
    part = http.calls[0][1]["json"]["messages"][0]["content"][1]
    assert part == {"type": "file", "file": {"file_data": "data:application/pdf;base64,AAAA", "filename": "supplier.pdf"}}


def test_invoice_provider_preserves_underscore_file_ids_for_pdf():
    http = Http(provider_payload())
    provider = MetaInvoiceVisionProvider("secret", "muse-spark-1.3", http)
    result = StructuredAI(None, invoice_provider=provider).invoice_extract(
        InvoiceImageRequest("file_123", "application/pdf", "supplier.pdf")
    )
    assert result.source == "provider"
    part = http.calls[0][1]["json"]["messages"][0]["content"][1]
    assert part == {"type": "file", "file": {"file_id": "file_123"}}


def test_product_matching_is_only_a_review_suggestion():
    http = Http(provider_payload())
    provider = MetaInvoiceVisionProvider("secret", "muse-spark-1.3", http)
    request = InvoiceImageRequest(
        "data:image/png;base64,AAAA", "image/png", "supplier.png",
        catalogue=(InvoiceCatalogueProduct("product-coke", "COKE-300", "Coca-Cola 300ml"),),
    )
    result = StructuredAI(None, invoice_provider=provider).invoice_extract(request)
    line = result.value.lines[0]
    assert line.suggested_product_id == "product-coke"
    assert line.match_status == "suggested"
    assert result.value.review_only is True


def test_invoice_provider_rejects_non_review_output():
    payload = provider_payload()
    raw = json.loads(payload["choices"][0]["message"]["content"])
    raw["review_only"] = False
    payload["choices"][0]["message"]["content"] = json.dumps(raw)
    result = StructuredAI(None, invoice_provider=MetaInvoiceVisionProvider("secret", "model", Http(payload))).invoice_extract(image_request())
    assert result.source == "fallback"
    assert result.value.status == "unavailable"
    assert result.reason == "invalid_or_unsafe_provider_response"


def test_invoice_image_is_not_configured_without_explicit_vision_model():
    ai = build_invoice_vision_ai(InvoiceVisionSettings("", "secret"))
    result = ai.invoice_extract(image_request())
    assert result.value.status == "provider_not_configured"
    assert result.value.review_only is True


def test_invoice_input_rejects_local_paths_but_accepts_pdf():
    ai = StructuredAI(None, invoice_provider=MetaInvoiceVisionProvider("secret", "model", Http(provider_payload())))
    local = ai.invoice_extract(InvoiceImageRequest("C:\\secret.png", "image/png"))
    assert local.reason == "schema_error"
