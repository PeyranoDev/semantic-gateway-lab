"""HTTP/SQL contracts. Optional dependencies are installed by the salon CI job."""
import base64
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import asdict
from threading import Barrier
import unittest

try:
    import fastapi, httpx
    HAS_HTTP = True
except ImportError:
    HAS_HTTP = False

from integrations.salon.model import Action, ACTORS, OPERATIONS, RESOURCES, PUBLIC_KEY, legitimate_seeds
from integrations.salon.oracle import check
from integrations.salon.feedback import project

@unittest.skipUnless(HAS_HTTP, "install backends/salon/requirements.lock")
class SalonHTTPTests(unittest.TestCase):
    def setUp(self):
        from integrations.salon.adapter import Adapter
        self.adapter = Adapter()

    def tearDown(self):
        self.adapter.close()

    def send(self, operation, actor="alice", resource="a"):
        action = Action(operation, actor, resource)
        before = self.adapter.snapshot()
        response = self.adapter.execute(action)
        after = self.adapter.snapshot()
        self.assertEqual(check(before, action, response, after), [], (action, response))
        return response

    def test_legitimate_workflows_and_four_mutations(self):
        from integrations.salon.adapter import Adapter
        from integrations.salon.checks import validate
        self.assertEqual(len(validate(self.adapter, "fixed")), 12)
        for variant in ("read_scope", "slot_capacity", "confirm_unpaid", "refund_replay"):
            adapter = Adapter(variant)
            try:
                self.assertEqual(len(validate(adapter, variant)), 12)
            finally:
                adapter.close()

    def test_all_initial_actions(self):
        for operation in OPERATIONS:
            for actor in ACTORS:
                for resource in RESOURCES:
                    self.adapter.reset()
                    self.send(operation, actor, resource)

    def test_same_tenant_customer_cannot_read_another_customer(self):
        with self.adapter.database.transaction() as conn:
            conn.execute("UPDATE bookings SET customer='bob' WHERE id='a2'")
        response = self.send("read_booking", "alice", "a2")
        self.assertEqual(response["status"], 404)

    def test_foreign_write_has_no_effect(self):
        self.send("reserve")
        before = self.adapter.snapshot()
        response = self.send("cancel", "staff_b")
        self.assertEqual(response["status"], 404)
        self.assertEqual(before, self.adapter.snapshot())

    def test_pay_charge_comes_from_server_and_cannot_repeat(self):
        self.send("reserve")
        self.assertEqual(self.send("pay")["status"], 200)
        self.assertEqual(self.send("pay")["status"], 409)
        state = self.adapter.snapshot()
        self.assertEqual(state["users"]["alice"]["balance"], 4000)
        self.assertEqual(len(state["ledger"]), 1)

    def test_full_lifecycle_and_refund_once(self):
        for op, actor in (("reserve", "alice"), ("pay", "alice"), ("confirm", "staff_a"),
                          ("cancel", "alice"), ("refund", "staff_a")):
            self.assertEqual(self.send(op, actor)["status"], 200)
        self.assertEqual(self.send("refund", "staff_a")["status"], 409)
        self.assertEqual(self.send("cancel")["status"], 409)
        state = self.adapter.snapshot()
        self.assertEqual(state["users"]["alice"]["balance"], 5000)
        self.assertEqual(state["slots"]["a"]["occupied"], 0)
        self.assertEqual(len(state["ledger"]), 2)

    def test_staff_and_customer_roles(self):
        self.send("reserve")
        self.assertEqual(self.send("pay", "staff_a")["status"], 403)
        self.send("pay")
        self.assertEqual(self.send("confirm")["status"], 403)
        self.assertEqual(self.send("confirm", "staff_a")["status"], 200)

    def test_full_slot_reopens_after_cancel(self):
        self.send("reserve")
        self.assertEqual(self.send("reserve", "alice", "a2")["status"], 409)
        self.send("cancel")
        self.assertEqual(self.send("reserve", "alice", "a2")["status"], 200)

    def test_real_create_then_business_workflow(self):
        response = self.adapter.client.post("/bookings", json={"slot": "a"},
                                            headers=self.adapter.headers["alice"])
        self.assertEqual(response.status_code, 201)
        identifier = response.json()["id"]
        self.assertEqual(response.json()["customer"], "alice")
        for op, actor in (("reserve", "alice"), ("pay", "alice"), ("confirm", "staff_a")):
            response = self.adapter.client.post("/bookings/" + identifier + "/" + op,
                                                headers=self.adapter.headers[actor])
            self.assertEqual(response.status_code, 200)
        self.assertEqual(self.adapter.snapshot()["users"]["alice"]["balance"], 4000)

    def test_create_rejects_foreign_slot_and_forged_body(self):
        before = self.adapter.snapshot()
        response = self.adapter.client.post("/bookings", json={"slot": "b"},
                                            headers=self.adapter.headers["alice"])
        self.assertEqual(response.status_code, 404)
        for field in ("tenant", "customer", "paid", "price"):
            response = self.adapter.client.post("/bookings", json={"slot": "a", field: "b"},
                                                headers=self.adapter.headers["alice"])
            self.assertEqual(response.status_code, 422)
        self.assertEqual(before, self.adapter.snapshot())

    def test_session_forgery_expiry_and_wrong_password(self):
        from backends.salon.auth import issue
        for token in ("garbage", "malformed.token", issue("alice", "wrong-signing-key" * 3),
                       issue("alice", PUBLIC_KEY, now=0)):
            response = self.adapter.client.get("/bookings/a",
                                                headers={"Authorization": "Bearer " + token})
            self.assertEqual(response.status_code, 401)
        response = self.adapter.client.post("/sessions", json={"username": "alice", "password": "wrong"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(self.send("read_booking", "anonymous")["status"], 401)

    def test_identity_role_comes_from_database(self):
        with self.adapter.database.transaction() as conn:
            conn.execute("UPDATE users SET role='unknown' WHERE id='alice'")
        response = self.adapter.client.get("/bookings/a", headers=self.adapter.headers["alice"])
        self.assertEqual(response.status_code, 403)

    def test_rollback_after_money_and_ledger_effects(self):
        self.send("reserve")
        self.send("pay")
        self.send("cancel")
        before = self.adapter.snapshot()
        def fail(operation):
            if operation == "refund":
                raise RuntimeError("injected failure after writes")
        self.adapter.app.state.service.after_effect = fail
        response = self.adapter.execute(Action("refund", "staff_a"))
        self.assertEqual(response["status"], 500)
        self.assertEqual(before, self.adapter.snapshot())
        self.adapter.app.state.service.after_effect = None
        self.assertEqual(self.send("refund", "staff_a")["status"], 200)

    def overlap(self, actions):
        barrier = Barrier(2)
        original = self.adapter.database.transaction
        @contextmanager
        def synchronized():
            barrier.wait(timeout=15)
            with original() as conn:
                yield conn
        self.adapter.database.transaction = synchronized
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(self.adapter.execute, a) for a in actions]
                return sorted(f.result(timeout=30)["status"] for f in futures)
        finally:
            self.adapter.database.transaction = original

    def test_two_concurrent_reservations_for_last_slot(self):
        codes = self.overlap([Action("reserve"), Action("reserve", "alice", "a2")])
        self.assertEqual(codes, [200, 409])
        state = self.adapter.snapshot()
        self.assertEqual(state["slots"]["a"]["occupied"], 1)
        self.assertEqual(sum(b["status"] == "reserved" for b in state["bookings"].values()), 1)

    def test_two_concurrent_refunds_credit_once(self):
        self.send("reserve")
        self.send("pay")
        self.send("cancel")
        codes = self.overlap([Action("refund", "staff_a"), Action("refund", "staff_a")])
        self.assertEqual(codes, [200, 409])
        state = self.adapter.snapshot()
        self.assertEqual(state["users"]["alice"]["balance"], 5000)
        self.assertEqual(sum(x["kind"] == "refund" for x in state["ledger"]), 1)

    def test_enabled_projection_loses_payment_identity(self):
        from integrations.salon.experiment import replay
        replay(self.adapter, [Action("reserve"), Action("pay")])
        left = self.adapter.snapshot()
        replay(self.adapter, [Action("reserve", "bob", "b"), Action("pay", "bob", "b")])
        right = self.adapter.snapshot()
        self.assertEqual(project(left, "sequence_enabled"), project(right, "sequence_enabled"))
        self.assertNotEqual(project(left, "sequence_enriched"), project(right, "sequence_enriched"))
        from integrations.salon.oracle import expected
        action = Action("confirm", "staff_a", "a")
        self.assertEqual(expected(left, action)[0], 200)
        self.assertEqual(expected(right, action)[0], 409)

    def test_campaign_reproducibility_and_witness(self):
        from integrations.salon.adapter import Adapter
        from integrations.salon.experiment import campaign
        adapter = Adapter("read_scope")
        try:
            first = campaign(adapter, "random", "BOOKING_SCOPE", 9123, 120)
            second = campaign(adapter, "random", "BOOKING_SCOPE", 9123, 120)
            first.pop("elapsed_s")
            second.pop("elapsed_s")
            self.assertEqual(first, second)
            self.assertTrue(first["detected"])
        finally:
            adapter.close()

class SalonPortableTests(unittest.TestCase):
    def test_generator_is_exact_transfer(self):
        from pathlib import Path
        root = Path(__file__).parents[1]
        self.assertEqual((root/"integrations/salon/generator.py").read_bytes(),
                         (root/"integrations/aoristo/generator.py").read_bytes())

    def test_seeds_and_action_domain(self):
        self.assertEqual(len(legitimate_seeds()), 8)
        self.assertEqual(sum(map(len, legitimate_seeds())), 24)
        for seed in legitimate_seeds():
            for action in seed:
                self.assertEqual(Action(**asdict(action)), action)
        with self.assertRaises(ValueError):
            Action("invalid")

if __name__ == "__main__":
    unittest.main()
