import ast
import copy
import json
from pathlib import Path
import unittest
from fuzzlab.abstraction import abstract
from fuzzlab.backend import Gateway
from fuzzlab.fuzzer import minimize, replay
from fuzzlab.model import Action, fixture_approval, initial_state
from fuzzlab.oracle import inspect
from fuzzlab.scenarios import legitimate_workflow, regression_witnesses

class SecurityTests(unittest.TestCase):
    def test_legitimate_workflow_reaches_effects(self):
        gateway = Gateway()
        for action in legitimate_workflow():
            before = gateway.state.snapshot()
            response = gateway.execute(action)
            self.assertTrue(response["allowed"], action)
            self.assertEqual(inspect(before, action, response, gateway.state.snapshot()), [])
        self.assertEqual(gateway.state.documents["d1"].content, "replacement")
        self.assertEqual(gateway.state.used_nonces, ["n1"])

    def test_unknown_authenticated_identity_denied(self):
        g = Gateway()
        a = Action("read_document", actor="unknown")
        before = g.state.snapshot()
        result = g.execute(a)
        self.assertFalse(result["allowed"])
        self.assertEqual(inspect(before, a, result, g.state.snapshot()), [])

    def test_unknown_tool_denied_and_audited(self):
        g = Gateway()
        a = Action("grant_admin")
        before = g.state.snapshot()
        response = g.execute(a)
        self.assertFalse(response["allowed"])
        self.assertEqual(inspect(before, a, response, g.state.snapshot()), [])

    def test_list_does_not_disclose_other_department(self):
        self.assertEqual(Gateway().execute(Action("list_documents"))["data"], ["d1", "d3"])

    def test_unshared_same_department_is_not_read_authority(self):
        self.assertFalse(Gateway().execute(Action("read_document", actor="mallory"))["allowed"])

    def test_approval_does_not_replace_owner_authorization(self):
        g = Gateway()
        g.execute(Action("request_delete"))
        token = fixture_approval(actor="bob")
        self.assertFalse(g.execute(Action("delete_document", actor="bob", token=token))["allowed"])

    def test_approval_bound_to_operation(self):
        envelope = json.loads(fixture_approval())
        envelope["payload"]["operation"] = "read_document"
        # An altered signed payload must fail regardless of the operation check.
        g = Gateway()
        g.execute(Action("request_delete"))
        self.assertFalse(g.execute(Action("delete_document", token=json.dumps(envelope)))["allowed"])

    def test_delete_shared_document_denied_even_with_signature(self):
        g = Gateway()
        g.execute(Action("request_delete"))
        g.execute(Action("initiate_share"))
        g.execute(Action("accept_share", actor="bob"))
        self.assertFalse(g.execute(Action("delete_document", token=fixture_approval()))["allowed"])

    def test_delete_requires_request(self):
        self.assertFalse(Gateway().execute(Action("delete_document", token=fixture_approval()))["allowed"])

    def test_cross_department_share_denied(self):
        self.assertFalse(Gateway().execute(Action("initiate_share", target="carol"))["allowed"])

    def test_expired_approval_denied(self):
        g = Gateway()
        g.execute(Action("request_delete"))
        self.assertFalse(g.execute(Action("delete_document", token=fixture_approval(expires=999)))["allowed"])

    def test_malformed_approval_denied(self):
        for token in ("", "{}", "[]", "null", "bad", '{"payload":null}', '{"payload":{},"mac":3}'):
            with self.subTest(token=token):
                g = Gateway()
                g.execute(Action("request_delete"))
                self.assertFalse(g.execute(Action("delete_document", token=token))["allowed"])

    def test_oracle_detects_denied_state_mutation(self):
        before = initial_state().snapshot()
        after = copy.deepcopy(before)
        action = Action("read_document", actor="bob")
        after["documents"]["d1"]["content"] = "leaked"
        after["audit"].append({"action": action.__dict__, "allowed": False})
        self.assertIn("DENY_MUTATED_STATE", inspect(before, action, {"allowed": False, "data": None}, after))

    def test_oracle_detects_authorized_operation_blocked(self):
        before = initial_state().snapshot()
        after = copy.deepcopy(before)
        action = Action("read_document")
        after["audit"].append({"action": action.__dict__, "allowed": False})
        self.assertIn("LEGITIMATE_TASK_BLOCKED", inspect(before, action, {"allowed": False, "data": None}, after))

    def test_oracle_detects_wrong_read_response(self):
        g = Gateway()
        a = Action("read_document")
        before = g.state.snapshot()
        response = g.execute(a)
        response["data"] = "wrong"
        self.assertIn("OUTPUT_MISMATCH", inspect(before, a, response, g.state.snapshot()))

    def test_oracle_does_not_import_backend_or_abstraction(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / "fuzzlab/oracle.py").read_text())
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertNotIn("backend", imports)
        self.assertNotIn("abstraction", imports)
        self.assertNotIn("scenarios", imports)

    def test_same_enabled_tools_different_recipient_relations(self):
        first = Gateway()
        second = Gateway()
        first.execute(Action("initiate_share", target="bob"))
        second.execute(Action("initiate_share", target="mallory"))
        s1, s2 = first.state.snapshot(), second.state.snapshot()
        self.assertEqual(abstract(s1, "enabled"), abstract(s2, "enabled"))
        self.assertNotEqual(abstract(s1, "enriched"), abstract(s2, "enriched"))
        # Concrete outcomes differ even though coarse labels agree.
        self.assertTrue(first.execute(Action("accept_share", actor="bob"))["allowed"])
        self.assertFalse(second.execute(Action("accept_share", actor="bob"))["allowed"])

    def test_minimizer_keeps_replay_violation(self):
        code, trace = regression_witnesses()["approval_replay"]
        sequence = [Action("list_documents")] + trace + [Action("list_documents")]
        minimal, cost = minimize(sequence, "approval_replay", code)
        self.assertGreater(cost, 0)
        self.assertEqual(len(minimal), 5)
        self.assertIn(code, replay(minimal, "approval_replay")["violations"])
        for i in range(len(minimal)):
            self.assertNotIn(code, replay(minimal[:i] + minimal[i+1:], "approval_replay")["violations"])

# Each injected implementation defect must violate the independent oracle,
# and the identical witness must be handled correctly by the fixed service.
def mutant_case(mutant, code, trace):
    def test(self):
        self.assertIn(code, replay(trace, mutant)["violations"])
    return test

def fixed_case(mutant, code, trace):
    def test(self):
        self.assertEqual(replay(trace)["violations"], [])
        g = Gateway()
        responses = [g.execute(a) for a in trace]
        self.assertFalse(responses[-1]["allowed"])
    return test

for name, (code, trace) in regression_witnesses().items():
    setattr(SecurityTests, f"test_mutant_{name}", mutant_case(name, code, trace))
    setattr(SecurityTests, f"test_fixed_blocks_{name}", fixed_case(name, code, trace))
