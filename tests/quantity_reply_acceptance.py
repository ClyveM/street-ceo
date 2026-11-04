"""Offline quantity grammar and narrowly qualified clarification targets."""
import pytest

from services.ai.catalogue_voice import resolve_catalogue_voice
from services.api.voice_boundary import parse_quantity_reply

CHIPS = [{"product_id": "chips", "name": "Potato chips", "sku": "CHIPS-100"}]


@pytest.mark.parametrize("heard,expected", [("one", 1), ("1", 1), ("One!", 1), ("twenty", 20), ("9999", 9999)])
def test_bare_explicit_quantity_needs_no_wake_phrase(heard, expected):
    assert parse_quantity_reply(heard) == expected


@pytest.mark.parametrize("heard", ["", "0", "zero", "-1", "1.5", "1 2", "one or two", "one coke", "10000", "true"])
def test_quantity_reply_never_infers_or_truncates(heard):
    assert parse_quantity_reply(heard) is None


@pytest.mark.parametrize("heard,qualified", [("putado chips naples", True), ("unicorn chips", False)])
def test_model_target_qualification_does_not_rely_on_one_similar_word(heard, qualified):
    class Provider:
        def complete(self, query):
            return {"segments": [{"segment_id": item["segment_id"], "product_id": "chips", "quantity": item["quantity"], "resolution": "uncertain"} for item in query.trusted_context["segments"]]}

    result = resolve_catalogue_voice(heard, CHIPS, provider=Provider(), allow_local_proposals=False)
    assert result.lines == ()
    assert (result.clarification_product_id == "chips") is qualified


def test_distinct_unknown_item_stays_pending_alongside_grounded_chips():
    class Provider:
        def complete(self, query):
            return {"segments": [{"segment_id": item["segment_id"], "product_id": "chips", "quantity": item["quantity"], "resolution": "uncertain"} for item in query.trusted_context["segments"]]}

    result = resolve_catalogue_voice("chips and unicorn", CHIPS, provider=Provider(), allow_local_proposals=False)
    assert result.status == "needs_clarification"
    assert result.lines == ()
    assert result.clarification_product_id == "chips"
    assert [(item.heard, item.product_id, item.quantity) for item in result.pending_items] == [
        ("chips", "chips", None),
        ("unicorn", None, None),
    ]
