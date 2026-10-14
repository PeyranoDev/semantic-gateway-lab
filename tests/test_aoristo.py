"""Portable harness tests; HTTP/PostgreSQL checks run separately with private source."""
import ast
import copy
import json
from pathlib import Path
import random
import unittest

from integrations.aoristo.experiment import campaign
from integrations.aoristo.feedback import project
from integrations.aoristo.generator import Mutator, OPERATORS
from integrations.aoristo.model import Action, legitimate_seeds, SOURCE_COMMIT
from integrations.aoristo.oracle import check
from integrations.aoristo.run import validate_config, paired
from integrations.aoristo.adapter import validate_database_url, clean_response

def fixture():
    return {"sales": {"a": {"grocery": 1, "status": "pending", "quantity": 3},
                      "b": {"grocery": 2, "status": "pending", "quantity": 3}},
            "inventory": {"1": 7, "2": 7},
            "invitations": {"a": {"unit": "a", "uses": 0, "max_uses": 1},
                            "b": {"unit": "b", "uses": 0, "max_uses": 1}}}

class BudgetDouble:
    """Used only for harness cost tests, not backend research results."""
    def reset(self): self.state = fixture()
    def snapshot(self): return copy.deepcopy(self.state)
    def execute(self, action):
        before = self.snapshot()
        body = {"data": {"id": {"a": 1, "b": 2}.get(action.resource)}}
        if check(before, action, {"status": 200, "body": body}, before):
            return {"status": 403, "body": {}}
        return {"status": 200, "body": body}

class AoristoHarnessTests(unittest.TestCase):
    def test_action_domain(self):
        with self.assertRaises(ValueError): Action("not-an-operation")

    def test_tenant_read(self):
        s = fixture()
        self.assertIn("READ_TENANT", check(s, Action("read_sale", "alice", "b"), {"status": 200,"body": {}}, s))

    def test_legitimate_read(self):
        s = fixture()
        self.assertEqual([], check(s, Action("read_sale"), {"status": 200,"body": {"data":{"id":1}}}, s))

    def test_cancel_once_effect(self):
        s = fixture(); after = copy.deepcopy(s)
        after["sales"]["a"]["status"] = "cancelled"; after["inventory"]["1"] = 10
        self.assertEqual([], check(s, Action("cancel_sale"), {"status": 200,"body": {}}, after))

    def test_cancel_replay(self):
        s = fixture(); s["sales"]["a"]["status"] = "cancelled"; s["inventory"]["1"] = 10
        after = copy.deepcopy(s); after["inventory"]["1"] = 13
        self.assertIn("CANCEL_REPLAY", check(s, Action("cancel_sale"), {"status":200,"body":{}}, after))

    def test_cross_tenant_cancel(self):
        s = fixture(); after = copy.deepcopy(s); after["sales"]["b"]["status"] = "cancelled"
        self.assertIn("CANCEL_TENANT", check(s, Action("cancel_sale","alice","b"), {"status":200,"body":{}}, after))

    def test_invitation_scope(self):
        s = fixture(); after = copy.deepcopy(s); del after["invitations"]["b"]
        self.assertIn("INVITATION_SCOPE", check(s, Action("revoke_invitation","ruth","b"), {"status":200,"body":{}}, after))

    def test_invitation_capability_is_public(self):
        s = fixture(); after = copy.deepcopy(s); after["invitations"]["a"]["uses"] = 1
        self.assertEqual([], check(s, Action("consume_invitation","anonymous"), {"status":200,"body":{}}, after))

    def test_invitation_limit_denial(self):
        s = fixture(); s["invitations"]["a"]["uses"] = 1
        self.assertEqual([], check(s, Action("consume_invitation","anonymous"), {"status":400,"body":{}}, s))

    def test_error_after_write(self):
        s = fixture(); after = copy.deepcopy(s)
        after["invitations"]["new-1"] = {"unit":"a","uses":0,"max_uses":1}
        self.assertIn("ERROR_EFFECT", check(s, Action("create_invitation","ruth"), {"status":500,"body":{}}, after))

    def test_projection_alias(self):
        a = fixture(); b = copy.deepcopy(a)
        b["sales"]["a"]["status"] = "cancelled"; b["inventory"]["1"] = 10
        self.assertEqual(project(a,"sequence_enabled"), project(b,"sequence_enabled"))
        self.assertNotEqual(project(a,"sequence_enriched"), project(b,"sequence_enriched"))

    def test_mutation_bounds_and_determinism(self):
        seeds = legitimate_seeds()
        for op in OPERATORS:
            a = Mutator(random.Random(17), 3); b = Mutator(random.Random(17), 3)
            result = a.mutate(seeds[0], seeds[1], op)
            self.assertEqual(result,b.mutate(seeds[0],seeds[1],op))
            self.assertTrue(1 <= len(result[0]) <= 3)

    def test_no_oracle_or_regression_import_in_generator(self):
        path = Path(__file__).parents[1]/"integrations/aoristo/generator.py"
        tree = ast.parse(path.read_text())
        imports = [node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
        self.assertFalse(any(x and ("oracle" in x or "regressions" in x) for x in imports))

    def test_budget_counts_every_execution(self):
        for mode in ("random","sequence_uniform","sequence_enabled","sequence_enriched"):
            row = campaign(BudgetDouble(), mode, "READ_TENANT", 17, 19)
            self.assertEqual(19,row["calls"])
            self.assertTrue(row["right_censored"])

    def test_small_budget(self):
        row = campaign(BudgetDouble(),"sequence_uniform","READ_TENANT",0,1)
        self.assertEqual(1,row["calls"]); self.assertEqual(1,row["bootstrap_calls"])

    def test_config_validation(self):
        config = json.loads((Path(__file__).parents[1]/"configs/aoristo-pilot.json").read_text())
        validate_config(config)
        config["source_commit"] = "other"
        with self.assertRaises(ValueError): validate_config(config)

    def test_matched_pair_censoring(self):
        rows = [{"target":"CANCEL_REPLAY","mode":m,"seed":0,"detected":hit,"calls":calls}
                for m,hit,calls in (("sequence_enabled",False,120),("sequence_enriched",True,30))]
        result = paired(rows)[0]
        self.assertEqual(1,result["right_only"])
        self.assertEqual(-90,result["mean_right_minus_left_capped_calls"])

    def test_source_lock(self):
        lock = json.loads((Path(__file__).parents[1]/"integrations/aoristo/source-lock.json").read_text())
        self.assertEqual(SOURCE_COMMIT,lock["expected_commit"])
        self.assertEqual(216,len(lock["app_files"]))

    def test_database_url_is_local_and_disposable(self):
        validate_database_url("postgresql://lab:lab@127.0.0.1:55432/sglab_fixture")
        validate_database_url("postgresql+psycopg2://lab:lab@localhost/sglab_fixture")

    def test_database_url_rejects_existing_application_name(self):
        with self.assertRaises(ValueError): validate_database_url("postgresql://lab:lab@localhost/verdusoft")

    def test_database_url_rejects_remote_host_and_query_redirect(self):
        for url in ("postgresql://lab:lab@db.example.org/sglab_fixture", "postgresql://lab:lab@localhost/sglab_fixture?host=db.example.org"):
            with self.assertRaises(ValueError): validate_database_url(url)

    def test_database_url_rejects_other_dialects(self):
        with self.assertRaises(ValueError): validate_database_url("sqlite:///:memory:")

    def test_response_normalization_preserves_schema_error(self):
        body = {"detail":"7 validation errors for InvitationResponse\nvolatile UUID and datetime"}
        self.assertEqual({"error":"InvitationResponse validation failed","validation_errors":7}, clean_response(body))
        self.assertEqual({"id":1}, clean_response({"id":1,"Token":"test-capability","date":"now"}))

if __name__ == "__main__": unittest.main()
