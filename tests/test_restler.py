"""Meaningful budget, identity, isolation and witness checks for the external harness."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

try:
    import fastapi, httpx
    HAS_HTTP = True
except ImportError:
    HAS_HTTP = False

from integrations.restler.spec import specification, RESTLER_COMMIT


class SpecificationTests(unittest.TestCase):
    def test_finite_routes_and_no_fault_programs(self):
        spec = specification()
        operations = [(p, method) for p, methods in spec["paths"].items() for method in methods]
        self.assertEqual(len(operations), 7)
        self.assertNotIn(("/bookings", "post"), operations)
        self.assertEqual(spec["openapi"], "3.0.3")
        self.assertNotIn("example", json.dumps(spec))
        self.assertEqual(len(RESTLER_COMMIT), 40)


@unittest.skipUnless(HAS_HTTP, "install backends/salon/requirements.lock")
class ObserverTests(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        from backends.salon.app import create_app
        from integrations.restler.server import Observer
        from integrations.salon.model import PUBLIC_KEY
        self.directory = TemporaryDirectory()
        self.output = Path(self.directory.name)
        self.app = create_app(self.output/"test.db", PUBLIC_KEY)
        self.app.state.database.provision_fixture()
        self.observer = Observer(self.app, self.output)
        self.client = TestClient(self.observer)
        self.client.__enter__()
        self.headers = {}
        for actor in ("alice", "bob", "staff_a", "staff_b"):
            response = self.client.post("/sessions", json={"username": actor, "password": "research-only-"+actor})
            self.headers[actor] = {"Authorization": "Bearer "+response.json()["access_token"]}
        self.start()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.directory.cleanup()

    def start(self, budget=100):
        self.client.post("/_lab/start", json={"phase": "search", "budget": budget}).raise_for_status()

    def send(self, op, actor="alice", resource="a", sequence="first"):
        path = "/bookings/"+resource + ("" if op == "read_booking" else "/"+op)
        headers = {**self.headers[actor], "x-restler-sequence-id": sequence}
        return self.client.request("GET" if op == "read_booking" else "POST", path, headers=headers)

    def events(self):
        return [json.loads(l) for l in (self.output/"http.jsonl").read_text().splitlines()]

    def test_new_sequence_resets_committed_state(self):
        self.assertEqual(self.send("reserve").status_code, 200)
        self.assertEqual(self.send("pay").status_code, 200)
        self.assertEqual(self.send("confirm", "staff_a").status_code, 200)
        self.assertEqual(self.app.state.database.snapshot()["users"]["alice"]["balance"], 4000)
        self.assertEqual(self.send("read_booking", sequence="second").json()["status"], "draft")
        self.assertEqual(self.app.state.database.snapshot()["users"]["alice"]["balance"], 5000)
        self.assertEqual(self.observer.episodes, 2)
        self.assertFalse(any(e.get("violations") for e in self.events()))

    def test_budget_gate_never_dispatches_extra_effect(self):
        self.start(budget=1)
        self.assertEqual(self.send("reserve").status_code, 200)
        before = self.app.state.database.snapshot()
        self.assertEqual(self.send("pay").status_code, 503)
        self.assertEqual(self.app.state.database.snapshot(), before)
        self.assertEqual(self.observer.calls, 1)
        self.assertEqual(sum(e["kind"] == "budget_gate" for e in self.events()), 1)

    def test_noncontiguous_or_missing_sequence_is_infrastructure_error(self):
        self.send("read_booking", sequence="first")
        self.send("read_booking", sequence="second")
        self.assertEqual(self.send("read_booking", sequence="first").status_code, 400)
        response = self.client.get("/bookings/a", headers=self.headers["alice"])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(self.observer.errors), 2)

    def test_reset_control_precedes_direct_sql_snapshot(self):
        self.send("reserve")
        self.client.post("/_lab/reset", headers={"x-lab-sequence": "second"}).raise_for_status()
        self.assertEqual(self.app.state.database.snapshot()["bookings"]["a"]["status"], "draft")
        self.assertEqual(self.send("reserve", sequence="second").status_code, 200)
        self.assertEqual(self.observer.episodes, 2)

    def test_oracle_detects_mutant_and_blocks_subsequent_search(self):
        self.app.state.service.variant = "confirm_unpaid"
        self.send("reserve")
        self.assertEqual(self.send("confirm", "staff_a").status_code, 200)
        self.assertTrue(self.observer.stopped)
        self.assertIn("CONFIRM_PAYMENT", self.events()[-1]["violations"])
        self.assertEqual(self.send("cancel").status_code, 503)
        self.client.post("/_lab/start", json={"phase": "replay"}).raise_for_status()
        self.assertEqual(self.send("reserve").status_code, 200)

    def test_signed_identity_and_session_values_never_enter_journal(self):
        self.assertEqual(self.send("read_booking", "bob").status_code, 404)
        event = self.events()[-1]
        self.assertEqual(event["action"]["actor"], "bob")
        content = (self.output/"http.jsonl").read_text()
        for headers in self.headers.values():
            self.assertNotIn(headers["Authorization"], content)
        self.assertNotIn("research-only-", content)

    def test_specification_routes_match_the_existing_backend(self):
        documented = {(method.upper(), path) for path, methods in specification()["paths"].items() for method in methods}
        actual = {(method, route.path) for route in self.app.routes if route.path.startswith("/bookings")
                  for method in route.methods if (method, route.path) != ("POST", "/bookings")}
        self.assertEqual(documented, actual)

    def test_outside_domain_is_counted_and_retained(self):
        response = self.client.post("/bookings", json={"slot": "a"},
                       headers={**self.headers["alice"], "x-restler-sequence-id": "first"})
        self.assertEqual(response.status_code, 201)
        event = self.events()[-1]
        self.assertEqual(event["domain"], "outside")
        self.assertEqual(self.observer.calls, 1)
        self.assertEqual(len(event["after"]["bookings"]), 5)

    def test_tcp_controls_and_campaign_with_exact_observer_replay(self):
        from integrations.restler.run import start_server, terminate, TCPAdapter, journal, characterize, revalidate
        from integrations.salon.checks import validate
        from integrations.salon_ablation.experiment import campaign
        with TemporaryDirectory() as directory:
            output = Path(directory)
            server, log = start_server("read_scope", output)
            adapter = None
            try:
                adapter = TCPAdapter(output)
                adapter.start("validation")
                self.assertEqual(len(validate(adapter, "read_scope")), 12)
                adapter.start("search", 120)
                offset = len(journal(output))
                result = campaign(adapter, "random", "ANY", 700, 120)
                observation = characterize(journal(output)[offset:])
                self.assertEqual(result["calls"], observation["calls"])
                self.assertTrue(observation["detected"])
                self.assertTrue(revalidate(adapter, observation))
            finally:
                if adapter:
                    adapter.close()
                terminate(server)
                log.close()
