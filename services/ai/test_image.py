import unittest

try:
    from services.ai.boundary import SocialImageRequest, SocialProduct, StructuredAI
    from services.ai.image import MetaMuseImageProvider, MuseImageSettings, SUPPORTED_MUSE_IMAGE_MODEL, audit_muse_image_configuration, build_muse_image_ai, generate_social_image
except ModuleNotFoundError:  # unittest discovery from services/ai
    from boundary import SocialImageRequest, SocialProduct, StructuredAI
    from image import MetaMuseImageProvider, MuseImageSettings, SUPPORTED_MUSE_IMAGE_MODEL, audit_muse_image_configuration, build_muse_image_ai, generate_social_image


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeHttp:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return FakeResponse(self.payload)


class ImageProvider:
    def __init__(self, value):
        self.value = value

    def generate_image(self, request):
        return self.value


def request(with_image=False):
    return SocialImageRequest(
        brief="Create a bright product image for a Facebook post.",
        products=(SocialProduct("coke-1", "Coca-Cola 300ml", image_ref="https://example.test/coke.png"),) if with_image else (SocialProduct("coke-1", "Coca-Cola 300ml"),),
        shop_image_ref="https://example.test/shop.png" if with_image else None,
    )


class ImageBoundaryTests(unittest.TestCase):
    def test_current_text_configuration_is_explicitly_not_image_capable(self):
        ai = build_muse_image_ai(MuseImageSettings("muse-spark-1.3", "secret"))
        result = generate_social_image(request(), ai=ai)
        self.assertEqual(result.value.status, "provider_not_configured")
        self.assertEqual(result.reason, "provider_not_configured")
        self.assertIn("text-only Llama", result.value.warnings[0])

    def test_only_the_documented_image_model_is_accepted(self):
        self.assertFalse(MuseImageSettings("muse-spark-1.3", "secret").image_capable)
        self.assertTrue(MuseImageSettings(SUPPORTED_MUSE_IMAGE_MODEL, "secret").image_capable)

    def test_configuration_audit_identifies_current_text_model(self):
        audit = audit_muse_image_configuration(MuseImageSettings("muse-spark-1.3", "secret"))
        self.assertEqual(audit.status, "unsupported_model")
        self.assertEqual(audit.expected_model, "muse-image-1.0")
        self.assertFalse(audit.live_access_verified)
        self.assertIn("muse-image-1.0", audit.reason)

    def test_configuration_audit_does_not_claim_entitlement(self):
        audit = audit_muse_image_configuration(MuseImageSettings("muse-image-1.0", "secret"))
        self.assertEqual(audit.status, "ready_for_smoke_test")
        self.assertFalse(audit.live_access_verified)
        self.assertTrue(audit.generation_endpoint.endswith("/v1/images/generations"))
        self.assertTrue(audit.edit_endpoint.endswith("/v1/images/edits"))

    def test_provider_uses_generation_endpoint_without_references(self):
        http = FakeHttp({"data": [{"url": "https://cdn.example.test/generated.png"}]})
        provider = MetaMuseImageProvider("secret", "muse-image-1.0", http)
        result = provider.generate_image(type("Request", (), {"image_refs": (), "prompt": "shop products", "size": "1024x1024", "output_format": "png"})())
        assert result["status"] == "draft"
        assert http.calls[0][0][0].endswith("/v1/images/generations")
        assert "images" not in http.calls[0][1]["json"]

    def test_provider_uses_edit_endpoint_for_product_or_shop_images(self):
        http = FakeHttp({"data": [{"b64_json": "aGVsbG8="}]})
        provider = MetaMuseImageProvider("secret", "muse-image-1.0", http)
        provider.generate_image(type("Request", (), {"image_refs": ("https://example.test/coke.png", "file_123"), "prompt": "shop products", "size": "1024x1024", "output_format": "png"})())
        call = http.calls[0]
        assert call[0][0].endswith("/v1/images/edits")
        assert call[1]["json"]["images"] == [{"image_url": "https://example.test/coke.png"}, {"file_id": "file_123"}]

    def test_generated_result_is_draft_only_and_keeps_product_scope(self):
        provider = ImageProvider({
            "status": "draft", "provider": "meta_muse_image", "model": "muse-image-1.0",
            "image_refs": ["https://cdn.example.test/generated.png"],
            "warnings": ["Not published."],
        })
        result = StructuredAI(None, image_provider=provider).social_image(request())
        self.assertEqual(result.source, "provider")
        self.assertTrue(result.value.draft_only)
        self.assertEqual(result.value.selected_product_ids, ("coke-1",))

    def test_large_base64_preview_is_accepted(self):
        provider = ImageProvider({
            "status": "draft", "provider": "meta_muse_image", "model": "muse-image-1.0",
            "image_refs": ["data:image/png;base64," + ("a" * 5000)],
            "warnings": ["Not published."],
        })
        result = StructuredAI(None, image_provider=provider).social_image(request())
        self.assertEqual(result.source, "provider")
        self.assertTrue(result.value.image_refs[0].startswith("data:image/png;base64,"))

    def test_local_file_reference_fails_closed(self):
        invalid = SocialImageRequest("Make an image", (SocialProduct("coke-1", "Coke", image_ref="C:\\secret.png"),))
        result = StructuredAI(None, image_provider=ImageProvider({})).social_image(invalid)
        self.assertEqual(result.source, "fallback")
        self.assertTrue(result.reason.startswith("schema_error:"))


if __name__ == "__main__":
    unittest.main()
