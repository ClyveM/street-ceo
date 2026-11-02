"""Offline provider deadline/capacity checks. Never creates a real provider."""
from concurrent.futures import Future, ThreadPoolExecutor
from threading import BoundedSemaphore, Event
from unittest.mock import patch

import pytest

from services.ai import catalogue_voice as voice

CATALOGUE = [{"product_id": "coke", "name": "Coca-Cola 300ml", "sku": "COKE-300"}]
RESPONSE = {"segments": [{"segment_id": 0, "product_id": "coke", "quantity": 1, "resolution": "matched"}]}


def resolve_provider(*args, **kwargs):
    """Exercise upstream behavior even when this phrase now has a local path."""
    return voice.resolve_catalogue_voice(*args, allow_local_proposals=False, **kwargs)


def test_timed_out_calls_hold_both_slots_until_completion_without_retry(monkeypatch):
    release = Event()
    calls = []

    class Slow:
        def complete(self, request):
            calls.append(request)
            assert release.wait(2), "test provider was not released"
            return RESPONSE

    capacity = BoundedSemaphore(2)
    with ThreadPoolExecutor(max_workers=2) as executor:
        monkeypatch.setattr(voice, "_EXECUTOR", executor)
        monkeypatch.setattr(voice, "_CAPACITY", capacity)
        try:
            first = resolve_provider("1 coke", CATALOGUE, provider=Slow(), timeout_seconds=.01)
            second = resolve_provider("1 coke", CATALOGUE, provider=Slow(), timeout_seconds=.01)
            busy = resolve_provider("1 coke", CATALOGUE, provider=Slow(), timeout_seconds=.01)
            assert first.reason == second.reason == "timeout"
            assert busy.reason == "provider_busy" and not busy.provider_called
            assert len(calls) == 2
            assert all(result.lines == () for result in (first, second, busy))
            assert not capacity.acquire(blocking=False)
        finally:
            release.set()
    # Late successful proposals cannot alter the already-returned timeout values.
    assert first.lines == second.lines == ()
    assert capacity.acquire(blocking=False)
    assert capacity.acquire(blocking=False)
    capacity.release()
    capacity.release()


def test_default_and_max_deadlines_fit_frontend_budget(monkeypatch):
    observed = []

    class CapturedFuture(Future):
        def result(self, timeout=None):
            observed.append(timeout)
            return super().result(timeout=timeout)

    class Inline:
        def submit(self, fn, *args):
            future = CapturedFuture()
            future.set_result(fn(*args))
            return future

    class Provider:
        def complete(self, request):
            return RESPONSE

    monkeypatch.setattr(voice, "_EXECUTOR", Inline())
    monkeypatch.setattr(voice, "_CAPACITY", BoundedSemaphore(2))
    assert resolve_provider("1 coke", CATALOGUE, provider=Provider()).status == "proposed"
    assert observed == [6.0]
    assert resolve_provider("1 coke", CATALOGUE, provider=Provider(), timeout_seconds=6).status == "proposed"
    with pytest.raises(ValueError):
        resolve_provider("1 coke", CATALOGUE, provider=Provider(), timeout_seconds=6.01)


def test_provider_exception_is_one_attempt_and_does_not_leak_details():
    calls = []

    class Broken:
        def complete(self, request):
            calls.append(request)
            raise RuntimeError("private upstream diagnostic")

    result = resolve_provider("1 coke", CATALOGUE, provider=Broken())
    assert len(calls) == 1
    assert result.status == "unavailable" and result.lines == ()
    assert result.provider_called
    assert "private" not in result.question


def test_unknown_apple_is_preserved_not_converted_to_coke():
    calls = []

    class Guess:
        def complete(self, request):
            calls.append(request)
            return RESPONSE

    result = resolve_provider("1 apple", CATALOGUE, provider=Guess())
    assert calls[0].untrusted_input == "1 apple"
    assert calls[0].trusted_context["segments"][0]["heard"] == "apple"
    assert result.status == "needs_clarification" and result.lines == ()


def test_unconfigured_provider_has_no_actionable_fallback():
    with patch.object(voice, "build_muse_ai", side_effect=AssertionError("must not build provider")):
        result = resolve_provider("1 coke", CATALOGUE, provider=None)
    assert result.status == "unavailable" and result.lines == ()
    assert not result.provider_called

