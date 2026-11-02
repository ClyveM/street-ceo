import unittest
from uuid import UUID, uuid4

try:
    from services.voice.state_machine import CatalogItem, CommandIntent, InputMode, SaleMode, SessionState, VoiceSession
except ModuleNotFoundError:  # direct unittest discovery within services/voice
    from state_machine import CatalogItem, CommandIntent, InputMode, SaleMode, SessionState, VoiceSession


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

    def create_sale(self, shop_id, lines, tender, idempotency_key, *, amount_received_cents=None):
        self.amount_received_cents = amount_received_cents
        self.calls.append((shop_id, list(lines), tender, idempotency_key))
        if self.failures:
            self.failures -= 1
            raise ConnectionError("provider unavailable")
        return self.responses.pop(0)


def make_session(intent=None, matches=None, gateway=None, mode=SaleMode.REVIEW, default_tender=None):
    product = CatalogItem(uuid4(), "Bread", 150, 10)
    return VoiceSession(
        uuid4(),
        Interpreter(intent or CommandIntent("record_sale", "bread", 2)),
        Catalog(matches if matches is not None else [product]),
        gateway or Gateway(),
        mode=mode,
        default_tender=default_tender,
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
            self.assertEqual(session.payment("cash", amount_minor=300).state, SessionState.COMMITTED)
        self.assertEqual(len(gateway.calls), 2)
        self.assertNotEqual(gateway.calls[0][3], gateway.calls[1][3])

    def test_missing_tender_does_not_post_and_basket_survives(self):
        gateway = Gateway()
        session = make_session(gateway=gateway)
        session.wake(); session.capture("bread"); session.end(); session.confirm(True)
        event = session.payment("")
        self.assertEqual(event.state, SessionState.PAYMENT)
        self.assertEqual(event.spoken, "I did not catch that. Please say cash or bank.")
        self.assertEqual(len(event.basket), 1)
        self.assertEqual(gateway.calls, [])

    def test_insufficient_cash_does_not_post_and_basket_survives(self):
        gateway = Gateway()
        session = make_session(gateway=gateway)
        session.wake(); session.capture("bread"); session.end(); session.confirm(True)
        event = session.payment("cash", amount_minor=299)
        self.assertEqual(event.state, SessionState.PAYMENT)
        self.assertIn("at least 300", event.spoken)
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
        session.end(); session.confirm(True); session.payment("cash", amount_minor=300)
        self.assertEqual(gateway.calls[0][1][0]["quantity"], 2)

        text_gateway = Gateway()
        text_session = make_session(gateway=text_gateway)
        self.assertEqual(text_session.accept(InputMode.TEXT, "submit", "bread").state, SessionState.QUOTE)
        text_session.confirm(True); text_session.payment("cash", amount_minor=300)
        self.assertEqual(text_gateway.calls[0][1][0]["quantity"], gateway.calls[0][1][0]["quantity"])
        self.assertEqual(text_gateway.calls[0][2], gateway.calls[0][2])

    def test_cancel_never_posts(self):
        gateway = Gateway()
        session = make_session(gateway=gateway)
        session.wake(); session.capture("bread"); session.end()
        event = session.confirm(False)
        self.assertEqual(event.state, SessionState.READY)
        self.assertEqual(gateway.calls, [])

    def test_quick_mode_apo_closing_commits_with_default_tender_and_receipt(self):
        gateway = Gateway()
        first = CatalogItem(uuid4(), "Coke", 150, 10)
        second = CatalogItem(uuid4(), "Sugar", 240, 10)

        class MultiInterpreter:
            def interpret(self, text):
                return CommandIntent("record_sale", "sugar" if "sugar" in text else "coke", 2 if "2" in text else 1)

        class MultiCatalog:
            def resolve(self, item):
                return [second if item == "sugar" else first]

        session = VoiceSession(uuid4(), MultiInterpreter(), MultiCatalog(), gateway, mode=SaleMode.QUICK, default_tender="bank")
        self.assertEqual(session.wake().state, SessionState.APO)
        self.assertEqual(session.capture("1 coke").state, SessionState.NAPO)
        self.assertEqual(session.capture("2 sugar").state, SessionState.NAPO)
        committed = session.end("Apo")
        self.assertEqual(committed.state, SessionState.COMMITTED)
        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(gateway.calls[0][2], "bank")
        self.assertEqual([line["quantity"] for line in gateway.calls[0][1]], [1, 2])
        self.assertEqual(committed.receipt["total_minor"], 630)

    def test_quick_mode_asks_only_for_missing_tender(self):
        gateway = Gateway()
        session = make_session(gateway=gateway, mode=SaleMode.QUICK)
        session.wake(); session.capture("bread")
        pending = session.end("Apo")
        self.assertEqual(pending.state, SessionState.PAYMENT)
        self.assertEqual(gateway.calls, [])
        committed = session.payment("bank")
        self.assertEqual(committed.state, SessionState.COMMITTED)

    def test_quick_mode_accepts_punctuated_apo_close(self):
        gateway = Gateway()
        session = make_session(gateway=gateway, mode=SaleMode.QUICK, default_tender="bank")
        session.wake(); session.capture("bread")
        committed = session.end("Apo.")
        self.assertEqual(committed.state, SessionState.COMMITTED)
        self.assertEqual(len(gateway.calls), 1)

    def test_quick_mode_ambiguity_never_autoposts_and_can_recover(self):
        gateway = Gateway()
        session = make_session(
            matches=[CatalogItem(uuid4(), "Bread", 150, 10), CatalogItem(uuid4(), "Bread loaf", 170, 10)],
            gateway=gateway,
            mode=SaleMode.QUICK,
            default_tender="bank",
        )
        session.wake()
        rejected = session.capture("bread")
        self.assertEqual(rejected.state, SessionState.FAILURE)
        self.assertEqual(gateway.calls, [])
        self.assertEqual(session.cancel().state, SessionState.READY)

    def test_quick_mode_provider_failure_preserves_retry_and_idempotency(self):
        gateway = Gateway(failures=1)
        session = make_session(gateway=gateway, mode=SaleMode.QUICK, default_tender="bank")
        session.wake(); session.capture("bread")
        failed = session.end("Apo")
        self.assertEqual(failed.state, SessionState.FAILURE)
        self.assertTrue(failed.retryable)
        retried = session.retry()
        self.assertEqual(retried.state, SessionState.COMMITTED)
        self.assertEqual(gateway.calls[0][3], gateway.calls[1][3])

    def test_undo_fails_closed_without_reversal_gateway(self):
        gateway = Gateway()
        session = make_session(gateway=gateway, mode=SaleMode.QUICK, default_tender="bank")
        session.wake(); session.capture("bread"); session.end("Apo")
        undone = session.undo_last_sale()
        self.assertEqual(undone.state, SessionState.FAILURE)
        self.assertIn("reversal service", undone.message)

    def test_cash_exact_and_overpayment_report_change(self):
        exact_gateway = Gateway()
        exact = make_session(gateway=exact_gateway)
        exact.wake(); exact.capture("bread"); exact.end(); exact.confirm(True)
        exact_result = exact.payment("cash 300")
        self.assertEqual(exact_result.state, SessionState.COMMITTED)
        self.assertEqual(exact_result.receipt["cash_received"], 300)
        self.assertEqual(exact_result.receipt["change_minor"], 0)

        over_gateway = Gateway()
        over = make_session(gateway=over_gateway)
        over.wake(); over.capture("bread"); over.end(); over.confirm(True)
        over_result = over.payment("cash 500")
        self.assertEqual(over_result.state, SessionState.COMMITTED)
        self.assertEqual(over_result.receipt["change_minor"], 200)

    def test_bank_has_no_cash_change(self):
        gateway = Gateway()
        session = make_session(gateway=gateway)
        session.wake(); session.capture("bread"); session.end(); session.confirm(True)
        result = session.payment("bank")
        self.assertEqual(result.state, SessionState.COMMITTED)
        self.assertIsNone(result.receipt["cash_received"])
        self.assertEqual(result.receipt["change_minor"], 0)

    def test_quick_cash_asks_amount_and_forwards_it(self):
        gateway = Gateway()
        session = make_session(gateway=gateway, mode=SaleMode.QUICK, default_tender="cash")
        session.wake(); session.capture("bread")
        pending = session.end("Apo")
        self.assertEqual(pending.state, SessionState.PAYMENT)
        self.assertIn("How much cash", pending.spoken)
        self.assertEqual(gateway.calls, [])
        result = session.payment("Cash, 500.")
        self.assertEqual(result.state, SessionState.COMMITTED)
        self.assertEqual(gateway.amount_received_cents, 500)
        self.assertEqual(result.receipt["change_minor"], 200)

    def test_gateway_tender_question_is_not_a_committed_sale(self):
        gateway = Gateway(responses=[{"status": "needs_tender", "question": "Cash or Bank?"}, {"id": str(uuid4())}])
        session = make_session(gateway=gateway, mode=SaleMode.QUICK)
        session.wake(); session.capture("bread"); session.end("Apo")
        pending = session.payment("bank")
        self.assertEqual(pending.state, SessionState.PAYMENT)
        self.assertIsNone(pending.sale_id)
        self.assertIsNone(pending.receipt)
        self.assertEqual(session.payment("cash 500").state, SessionState.COMMITTED)
        self.assertEqual(gateway.calls[0][3], gateway.calls[1][3])

    def test_missing_sale_id_never_reports_success(self):
        session = make_session(gateway=Gateway(responses=[{}]))
        session.wake(); session.capture("bread"); session.end(); session.confirm(True)
        self.assertEqual(session.payment("bank").state, SessionState.FAILURE)

    def test_receipt_uses_authoritative_change_and_new_cycle_clears_it(self):
        gateway = Gateway(responses=[{"id": str(uuid4()), "total_cents": 350, "amount_received_cents": 500, "change_cents": 150}])
        session = make_session(gateway=gateway)
        session.wake(); session.capture("bread"); session.end(); session.confirm(True)
        result = session.payment("cash 500")
        self.assertEqual(result.receipt["change_minor"], 150)
        self.assertEqual(result.receipt["total_minor"], 350)
        self.assertIsNone(session.wake().receipt)

    def test_unconfirmed_undo_preserves_sale_and_stable_retry_key(self):
        class RetryUndoGateway(Gateway):
            def __init__(self):
                super().__init__()
                self.undo_keys = []
            def undo_sale(self, shop_id, sale_id, idempotency_key):
                self.undo_keys.append(idempotency_key)
                return {} if len(self.undo_keys) == 1 else {"status": "reversed"}
        gateway = RetryUndoGateway()
        session = make_session(gateway=gateway, mode=SaleMode.QUICK, default_tender="bank")
        session.wake(); session.capture("bread"); session.end("Apo")
        pending = session.undo_last_sale()
        self.assertEqual(pending.state, SessionState.COMMITTED)
        self.assertTrue(pending.retryable)
        self.assertIsNotNone(pending.sale_id)
        self.assertEqual(session.undo_last_sale().state, SessionState.READY)
        self.assertEqual(gateway.undo_keys[0], gateway.undo_keys[1])

    def test_undo_success_calls_gateway_once_and_resets_session(self):
        class ReversibleGateway(Gateway):
            def undo_sale(self, shop_id, sale_id, idempotency_key):
                self.undo_call = (shop_id, sale_id, idempotency_key)
                return {"status": "reversed"}
        gateway = ReversibleGateway()
        session = make_session(gateway=gateway, mode=SaleMode.QUICK, default_tender="bank")
        session.wake(); session.capture("bread")
        sale = session.end("Apo")
        self.assertEqual(session.undo_last_sale().state, SessionState.READY)
        self.assertEqual(gateway.undo_call[1], sale.sale_id)
        self.assertEqual(gateway.undo_call[2], f"undo-{sale.sale_id}")
        self.assertEqual(session.undo_last_sale().state, SessionState.FAILURE)

    def test_unclear_tender_stays_in_payment_and_can_recover(self):
        gateway = Gateway()
        session = make_session(gateway=gateway)
        session.wake(); session.capture("bread"); session.end(); session.confirm(True)
        unclear = session.payment("maybe card")
        self.assertEqual(unclear.state, SessionState.PAYMENT)
        self.assertTrue(unclear.retryable)
        self.assertEqual(gateway.calls, [])
        self.assertEqual(session.payment("cash", amount_minor=300).state, SessionState.COMMITTED)


if __name__ == "__main__":
    unittest.main()
