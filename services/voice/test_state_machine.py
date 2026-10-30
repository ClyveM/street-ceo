import unittest
from uuid import UUID, uuid4

from state_machine import CatalogItem, CommandIntent, InputMode, SessionState, VoiceSession


class Interpreter:
    def __init__(self, intent):
        self.intent = intent

    def interpret(self, text):
        return self.intent


class Catalog:
    def __init__(self, matches):
        self.matches = matches

    def resolve(self, item):
        return self.matches


class Gateway:
    def __init__(self, responses=None, failures=0):
        self.calls = []
        self.responses = responses or [{"id": str(uuid4())}]
        self.failures = failures

    def create_sale(self, shop_id, lines, tender, idempotency_key):
        self.calls.append((shop_id, list(lines), tender, idempotency_key))
        if self.failures:
            self.failures -= 1
            raise ConnectionError("provider unavailable")
        return self.responses.pop(0)


def make_session(intent=None, matches=None, gateway=None):
    product = CatalogItem(uuid4(), "Bread", 150, 10)
    return VoiceSession(
        uuid4(),
        Interpreter(intent or CommandIntent("record_sale", "bread", 2)),
        Catalog(matches if matches is not None else [product]),
        gateway or Gateway(),
    )


class VoiceStateMachineTests(unittest.TestCase):
    def test_two_sequential_customer_cycles(self):
        gateway = Gateway(responses=[{"id": str(uuid4())}, {"id": str(uuid4())}])
        session = make_session(gateway=gateway)
        for _ in range(2):
            self.assertEqual(session.wake().state, SessionState.APO)
            self.assertEqual(session.capture("two bread").state, SessionState.NAPO)
            self.assertEqual(session.end().state, SessionState.QUOTE)
            self.assertEqual(session.confirm(True).state, SessionState.PAYMENT)
            self.assertEqual(session.payment("cash").state, SessionState.COMMITTED)
        self.assertEqual(len(gateway.calls), 2)
        self.assertNotEqual(gateway.calls[0][3], gateway.calls[1][3])

    def test_missing_tender_does_not_post_and_basket_survives(self):
        gateway = Gateway()
        session = make_session(gateway=gateway)
        session.wake(); session.capture("bread"); session.end(); session.confirm(True)
        event = session.payment("")
        self.assertEqual(event.state, SessionState.FAILURE)
        self.assertEqual(len(event.basket), 1)
        self.assertEqual(gateway.calls, [])

    def test_insufficient_cash_does_not_post_and_basket_survives(self):
        gateway = Gateway()
        session = make_session(gateway=gateway)
        session.wake(); session.capture("bread"); session.end(); session.confirm(True)
        event = session.payment("cash", amount_minor=299)
        self.assertEqual(event.state, SessionState.FAILURE)
        self.assertEqual(len(event.basket), 1)
        self.assertEqual(gateway.calls, [])

    def test_ambiguity_and_insufficient_stock_are_safe(self):
        ambiguous = make_session(matches=[CatalogItem(uuid4(), "Bread", 150, 10), CatalogItem(uuid4(), "Bread loaf", 170, 10)])
        ambiguous.wake()
        event = ambiguous.capture("bread")
        self.assertEqual(event.state, SessionState.FAILURE)
        self.assertEqual(event.basket, ())
        scarce = make_session(matches=[CatalogItem(uuid4(), "Bread", 150, 1)])
        scarce.wake()
        event = scarce.capture("bread")
        self.assertEqual(event.state, SessionState.FAILURE)
        self.assertEqual(event.basket, ())

    def test_provider_outage_preserves_basket_and_retry_reuses_key(self):
        gateway = Gateway(failures=1)
        session = make_session(gateway=gateway)
        session.wake(); session.capture("bread"); session.end(); session.confirm(True)
        failed = session.payment("bank")
        self.assertEqual(failed.state, SessionState.FAILURE)
        self.assertTrue(failed.retryable)
        self.assertEqual(len(failed.basket), 1)
        committed = session.retry()
        self.assertEqual(committed.state, SessionState.COMMITTED)
        self.assertEqual(gateway.calls[0][3], gateway.calls[1][3])
        self.assertEqual(gateway.calls[0][2], "bank")

    def test_fallback_modes_map_to_same_sale_contract(self):
        gateway = Gateway()
        session = make_session(gateway=gateway)
        self.assertEqual(session.accept(InputMode.PUSH_TO_TALK, "press").state, SessionState.APO)
        self.assertEqual(session.accept(InputMode.PUSH_TO_TALK, "release", "bread").state, SessionState.NAPO)
        session.end(); session.confirm(True); session.payment("cash")
        self.assertEqual(gateway.calls[0][1][0]["quantity"], 2)

        text_gateway = Gateway()
        text_session = make_session(gateway=text_gateway)
        self.assertEqual(text_session.accept(InputMode.TEXT, "submit", "bread").state, SessionState.QUOTE)
        text_session.confirm(True); text_session.payment("cash")
        self.assertEqual(text_gateway.calls[0][1][0]["quantity"], gateway.calls[0][1][0]["quantity"])
        self.assertEqual(text_gateway.calls[0][2], gateway.calls[0][2])

    def test_cancel_never_posts(self):
        gateway = Gateway()
        session = make_session(gateway=gateway)
        session.wake(); session.capture("bread"); session.end()
        event = session.confirm(False)
        self.assertEqual(event.state, SessionState.READY)
        self.assertEqual(gateway.calls, [])


if __name__ == "__main__":
    unittest.main()
