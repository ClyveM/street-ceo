"""Independent fast-path exclusions and confirmation-only provenance."""
import pytest

from services.ai.catalogue_voice import resolve_catalogue_voice

CATALOGUE = [
    {"product_id": "bread", "name": "Bread loaf", "sku": "BREAD-700"},
    {"product_id": "coke", "name": "Coca-Cola 300ml", "sku": "COKE-300"},
]


@pytest.mark.parametrize("phrase,expected", [
    ("1 bread glove number", [("bread", 1)]),
    ("2 coca-cola nabo marble", [("coke", 2)]),
    ("1 coke 2 bread", [("coke", 1), ("bread", 2)]),
])
def test_local_proposals_are_complete_and_confirmation_only(phrase, expected):
    result = resolve_catalogue_voice(phrase, CATALOGUE, provider=None)
    assert result.status == "proposed"
    assert [(line.product_id, line.quantity) for line in result.lines] == expected
    assert result.requires_confirmation and not result.provider_called
    assert result.source == "local_catalogue_proposal"
    assert "yes" in result.question.lower()


@pytest.mark.parametrize("phrase", [
    "1 apple", "1 apple coke", "1 coke apple", "1 coke 1 unicorn",
    "1 coke and unicorn", "1 coke 2", "0 coke", "1 coke 1 coke",
    "1 boke", "1 bread glove arbitrary", "1 coke 2 bread apple",
])
def test_unknown_partial_duplicate_and_typo_baskets_never_local_propose(phrase):
    result = resolve_catalogue_voice(phrase, CATALOGUE, provider=None)
    assert result.status != "proposed" and result.lines == ()
    assert not result.provider_called


@pytest.mark.parametrize("name", ["Number", "Glove", "Marble", "Nabo"])
def test_observed_noise_that_is_a_catalogue_product_is_not_discarded(name):
    catalogue = CATALOGUE + [{"product_id": "extra", "name": name, "sku": "EXTRA"}]
    phrase = "1 bread glove number" if name in {"Number", "Glove"} else "1 coke nabo marble"
    result = resolve_catalogue_voice(phrase, catalogue, provider=None)
    assert result.status != "proposed" and result.lines == ()


def test_missing_quantity_remains_no_line_question_and_alias_collision_rejects():
    result = resolve_catalogue_voice("coke", CATALOGUE, provider=None)
    assert result.reason == "missing_quantity" and result.lines == ()
    catalogue = CATALOGUE + [{"product_id": "brown", "name": "Bread brown", "sku": "BROWN"}]
    result = resolve_catalogue_voice("1 bread", catalogue, provider=None)
    assert result.status != "proposed" and result.lines == ()
