import base64
from uuid import UUID

import pytest
from fastapi import HTTPException

from services.api.app import InMemoryStore, SaleLine, ShopCreate, create_app
from services.api.persistence import Settings
from services.api.voice_boundary import VoiceAudioRequest, VoiceSaleCommitRequest, VoiceSaleCommitLine, VoiceSaleUndoRequest, VoiceTenderQuestion, VoiceTranscriptRequest


class FakeInterpreter:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def interpret(self, text):
        self.calls += 1
        return self.result


class Intent:
    action = "record_sale"
    item = "Bread"
    quantity = 2
    price_override_minor = None
    needs_confirmation = False


def setup_voice(interpreter=None):
    app = create_app(InMemoryStore(), Settings(voice_enabled=True), voice_interpreter=interpreter)
    create_shop = next(route.endpoint for route in app.routes if route.path == "/shops")
    shop = create_shop(ShopCreate(name="Voice Shop"))
    record = app.state.store.shops[shop.id]
    transcript = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/transcript")
    audio = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/audio")
    return app, shop, record, transcript, audio


def test_transcript_returns_bounded_intent_and_never_posts_sale():
    interpreter = FakeInterpreter(Intent())
    _, shop, record, endpoint, _ = setup_voice(interpreter)
    response = endpoint(VoiceTranscriptRequest(transcript="sell two bread"), record, "voice-1")
    assert response.shop_id == shop.id
    assert response.status == "needs_confirmation"
    assert response.intent.action == "record_sale"
    assert response.intent.needs_confirmation is True
    assert record.idempotent_sales == {}
    assert interpreter.calls == 1


def test_transcript_replay_is_idempotent_and_changed_payload_conflicts():
    interpreter = FakeInterpreter(Intent())
    _, _, record, endpoint, _ = setup_voice(interpreter)
    request = VoiceTranscriptRequest(transcript="sell two bread")
    first = endpoint(request, record, "voice-1")
    replay = endpoint(request, record, "voice-1")
    assert replay == first
    assert interpreter.calls == 1
    with pytest.raises(HTTPException, match="payload mismatch"):
        endpoint(VoiceTranscriptRequest(transcript="sell three bread"), record, "voice-1")


def test_audio_boundary_validates_and_returns_safe_unavailable_status():
    _, shop, record, _, endpoint = setup_voice()
    audio = base64.b64encode(b"fixture-audio").decode()
    response = endpoint(VoiceAudioRequest(audio_base64=audio), record, "audio-1")
    assert response.shop_id == shop.id
    assert response.status == "unavailable"
    assert response.error == "audio_transcription_unavailable"
    assert response.transcript is None


def test_audio_replay_and_invalid_payload_are_safe():
    _, _, record, _, endpoint = setup_voice()
    request = VoiceAudioRequest(audio_base64=base64.b64encode(b"fixture-audio").decode())
    first = endpoint(request, record, "audio-1")
    assert endpoint(request, record, "audio-1") == first
    with pytest.raises(HTTPException, match="payload mismatch"):
        endpoint(VoiceAudioRequest(audio_base64=base64.b64encode(b"different").decode()), record, "audio-1")


def test_voice_disabled_returns_not_found():
    app = create_app(InMemoryStore(), Settings(voice_enabled=False))
    shop_endpoint = next(route.endpoint for route in app.routes if route.path == "/shops")
    shop = shop_endpoint(ShopCreate(name="Disabled Voice Shop"))
    record = app.state.store.shops[shop.id]
    endpoint = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/transcript")
    with pytest.raises(HTTPException) as error:
        endpoint(VoiceTranscriptRequest(transcript="sell bread"), record, "voice-1")
    assert error.value.status_code == 404


def test_typed_multi_item_command_resolves_coke_and_sugar_from_catalogue():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings(voice_enabled=True), voice_interpreter=None)
    record = store.shops[shop_id]
    endpoint = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/transcript")

    response = endpoint(
        VoiceTranscriptRequest(transcript="2 coke 2 sugar"),
        record,
        "voice-aliases-1",
    )

    assert response.status == "needs_confirmation"
    assert [(line.product_name, line.quantity) for line in response.lines] == [
        ("Coca-Cola 300ml", 2),
        ("Sugar 1kg", 2),
    ]
    assert response.error is None
    assert response.error_code is None


def test_typed_apo_flow_resolves_hyphenated_coca_cola_from_catalogue():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings(voice_enabled=True), voice_interpreter=None)
    record = store.shops[shop_id]
    endpoint = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/transcript")

    response = endpoint(
        VoiceTranscriptRequest(transcript="1 sugar 1 Coca-Cola"),
        record,
        "voice-apo-sugar-coca-cola-1",
    )

    assert response.status == "needs_confirmation"
    assert [(line.product_name, line.quantity) for line in response.lines] == [
        ("Sugar 1kg", 1),
        ("Coca-Cola 300ml", 1),
    ]
    assert response.error is None
    assert response.error_code is None


def test_invalid_provider_response_returns_human_safe_error_and_code():
    class InvalidInterpreter:
        def interpret(self, text):
            return object()

    _, _, record, endpoint, _ = setup_voice(InvalidInterpreter())
    response = endpoint(VoiceTranscriptRequest(transcript="a strange command"), record, "voice-invalid-1")

    assert response.status == "rejected"
    assert response.error_code == "invalid_or_unsafe_provider_response"
    assert response.error is not None
    assert response.error != "invalid_or_unsafe_provider_response"
    assert "safely understand" in response.error


def test_reviewed_apo_basket_commits_once_and_decrements_stock():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings(voice_enabled=True), voice_interpreter=None)
    record = store.shops[shop_id]
    transcript = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/transcript")
    commit = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/commit")

    review = transcript(VoiceTranscriptRequest(transcript="Apo 1 coke 2 sugar Apo"), record, "review-apo-1")
    assert review.status == "needs_confirmation"
    assert [(line.product_name, line.quantity) for line in review.lines] == [
        ("Coca-Cola 300ml", 1), ("Sugar 1kg", 2)
    ]
    coke = next(product for product in record.products.values() if product.sku == "COKE-300")
    sugar = next(product for product in record.products.values() if product.sku == "SUGAR-1KG")
    before = (coke.stock_qty, sugar.stock_qty)
    request = VoiceSaleCommitRequest(
        review_id=review.request_id,
        lines=[VoiceSaleCommitLine(product_id=line.product_id, quantity=line.quantity) for line in review.lines],
        tender="cash", amount_received_cents=630,
    )
    sale = commit(request, record, "voice-sale-apo-1")
    assert sale.total_cents == 630
    assert (coke.stock_qty, sugar.stock_qty) == (before[0] - 1, before[1] - 2)
    replay = commit(request, record, "voice-sale-apo-1")
    assert replay.id == sale.id
    assert (coke.stock_qty, sugar.stock_qty) == (before[0] - 1, before[1] - 2)
    with pytest.raises(HTTPException, match="already committed"):
        commit(request, record, "voice-sale-apo-second-key")
    assert (coke.stock_qty, sugar.stock_qty) == (before[0] - 1, before[1] - 2)
    with pytest.raises(HTTPException, match="payload mismatch"):
        commit(request.model_copy(update={"amount_received_cents": 700}), record, "voice-sale-apo-1")
    # Receipt replay remains stable even if catalogue prices change later.
    coke.unit_price_cents += 100
    assert commit(request, record, "voice-sale-apo-1") == sale


def test_voice_commit_requires_a_review():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings(voice_enabled=True), voice_interpreter=None)
    record = store.shops[shop_id]
    commit = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/commit")
    with pytest.raises(HTTPException, match="review"):
        commit(VoiceSaleCommitRequest(review_id=UUID(int=0), lines=[VoiceSaleCommitLine(product_id=UUID(int=1), quantity=1)]), record, "voice-unreviewed")


def test_voice_commit_validates_tender_and_preserves_stock_on_failure():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings(voice_enabled=True), voice_interpreter=None)
    record = store.shops[shop_id]
    transcript = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/transcript")
    commit = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/commit")
    coke = next(product for product in record.products.values() if product.sku == "COKE-300")

    assert VoiceSaleCommitRequest(review_id=UUID(int=0), tender="credit", lines=[VoiceSaleCommitLine(product_id=coke.id, quantity=1)]).tender == "credit"
    review = transcript(VoiceTranscriptRequest(transcript="99 coke 1 sugar"), record, "voice-review-stock")
    with pytest.raises(HTTPException, match="insufficient stock"):
        commit(VoiceSaleCommitRequest(review_id=review.request_id, tender="bank", lines=[VoiceSaleCommitLine(product_id=line.product_id, quantity=line.quantity) for line in review.lines]), record, "voice-sale-stock")
    assert record.products[coke.id].stock_qty == 18


def test_apo_commit_has_audited_undo_with_idempotent_replay_and_duplicate_guard():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings(voice_enabled=True), voice_interpreter=None)
    record = store.shops[shop_id]
    transcript = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/transcript")
    commit = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/commit")
    undo = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/commit/{sale_id}/undo")
    coke = next(product for product in record.products.values() if product.sku == "COKE-300")
    before = coke.stock_qty
    review = transcript(VoiceTranscriptRequest(transcript="Apo 1 coke Apo"), record, "voice-undo-review")
    request = VoiceSaleCommitRequest(
        review_id=review.request_id,
        lines=[VoiceSaleCommitLine(product_id=review.lines[0].product_id, quantity=1)],
        tender="bank",
    )
    sale = commit(request, record, "voice-undo-sale")
    assert coke.stock_qty == before - 1
    undo_request = VoiceSaleUndoRequest(actor="owner", reason="wrong item recorded", confirmed=True)
    reversal = undo(sale.id, undo_request, record, "voice-undo-key")
    assert reversal.original_sale_id == sale.id
    assert reversal.audit_id == reversal.reversal_id
    assert reversal.status == "reversed"
    assert coke.stock_qty == before
    assert undo(sale.id, undo_request, record, "voice-undo-key") == reversal
    with pytest.raises(HTTPException, match="already reversed"):
        undo(sale.id, undo_request, record, "voice-undo-key-2")
    with pytest.raises(HTTPException, match="payload mismatch"):
        undo(sale.id, undo_request.model_copy(update={"reason": "changed reason"}), record, "voice-undo-key")


def test_voice_commit_returns_tender_question_and_validates_cash_change():
    store = InMemoryStore()
    shop_id = store.seed_demo_shop()
    app = create_app(store, Settings(voice_enabled=True), voice_interpreter=None)
    record = store.shops[shop_id]
    transcript = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/transcript")
    commit = next(route.endpoint for route in app.routes if route.path == "/api/v1/shops/{shop_id}/voice/commit")
    review = transcript(VoiceTranscriptRequest(transcript="Apo 1 coke Apo"), record, "tender-question-review")
    lines = [VoiceSaleCommitLine(product_id=review.lines[0].product_id, quantity=1)]
    question = commit(VoiceSaleCommitRequest(review_id=review.request_id, lines=lines), record, "tender-question")
    assert isinstance(question, VoiceTenderQuestion)
    assert question.status == "needs_tender"
    assert question.missing == ["tender"]
    with pytest.raises(HTTPException, match="insufficient_cash"):
        commit(VoiceSaleCommitRequest(review_id=review.request_id, lines=lines, tender="cash", amount_received_cents=149), record, "tender-short")
    sale = commit(VoiceSaleCommitRequest(review_id=review.request_id, lines=lines, tender="cash", amount_received_cents=200), record, "tender-cash")
    assert sale.amount_received_cents == 200
    assert sale.change_cents == 50
    assert commit(VoiceSaleCommitRequest(review_id=review.request_id, lines=lines, tender="cash", amount_received_cents=200), record, "tender-cash").id == sale.id
