import ast
import copy
from pathlib import Path
import unittest
from integrations.salon_portfolio.programs import Scheduler, MODES
from integrations.salon_portfolio.analysis import effects

try:
    import fastapi, httpx
    HAS_HTTP = True
except ImportError:
    HAS_HTTP = False

class PortfolioPortableTests(unittest.TestCase):
    def test_interleaving_preserves_both_component_streams_and_cost_balance(self):
        combined = Scheduler("portfolio_balanced",91201)
        separate = {m:Scheduler(m,91201) for m in MODES[:2]}
        for _ in range(300):
            arm,program,bootstrap,operator = combined.next()
            self.assertEqual((arm,program,bootstrap,operator), separate[arm].next())
            combined.charge(arm,len(program))
            self.assertLessEqual(abs(combined.calls["random"]-combined.calls["sequence_uniform"]),8)
        self.assertEqual(combined.seed_index,8)

    def test_scheduler_has_no_access_to_oracle_responses_or_mutant(self):
        source = (Path(__file__).parents[1]/"integrations/salon_portfolio/programs.py").read_text()
        imports = [n.module for n in ast.walk(ast.parse(source)) if isinstance(n,ast.ImportFrom)]
        self.assertEqual(imports,["integrations.salon.generator","integrations.salon.model"])
        for token in ("VARIANT_TARGET","oracle","response","violations"):
            self.assertNotIn(token,source.split('"""',2)[-1])

    def test_invalid_costs_and_modes_fail(self):
        with self.assertRaises(ValueError):
            Scheduler("unknown",1)
        scheduler = Scheduler("random",1)
        for calls in (0,9,True,-1):
            with self.assertRaises(ValueError):
                scheduler.charge("random",calls)

    def test_effects_keep_budgets_separate_and_are_json_stable(self):
        import json
        rows = [{"variant":"read_scope","budget":b,"mode":m,"seed":s,
                 "detected":m=="portfolio_balanced","calls":5 if m=="portfolio_balanced" else b}
                for b in (120,480) for m in MODES for s in range(4)]
        result = effects(rows,samples=20)
        self.assertEqual(len(result),4)
        self.assertEqual(json.loads(json.dumps(result)),result)
        for row in result:
            self.assertEqual(row["descriptive95_detection"],[1,1])
            self.assertEqual(row["descriptive95_capped_calls"],[5-row["budget"]]*2)

@unittest.skipUnless(HAS_HTTP,"install salon requirements")
class PortfolioHTTPTests(unittest.TestCase):
    def test_standalone_components_match_previous_implementation_exactly(self):
        from integrations.salon.adapter import Adapter
        from integrations.salon_ablation.experiment import campaign as previous
        from integrations.salon_portfolio.experiment import campaign
        for variant in ("fixed","read_scope","refund_replay"):
            adapter = Adapter(variant)
            try:
                for mode in MODES[:2]:
                    old = previous(adapter,mode,"ANY",91202,80)
                    new = campaign(adapter,mode,91202,80)
                    for row in (old,new):
                        row.pop("elapsed_s")
                    new.pop("arm_calls")
                    new.pop("episode_ledger")
                    self.assertEqual(old,new,(variant,mode))
            finally:
                adapter.close()

    def test_partial_episode_budget_charges_and_ledger_tampering(self):
        from integrations.salon.adapter import Adapter
        from integrations.salon_portfolio.experiment import campaign
        from scripts.verify_salon_portfolio import verify_ledger
        adapter = Adapter()
        try:
            for budget in (1,7,25,61):
                row = campaign(adapter,"portfolio_balanced",91203,budget)
                self.assertFalse(row["detected"])
                self.assertEqual(row["calls"],budget)
                self.assertEqual(sum(row["arm_calls"].values()),budget)
                verify_ledger(row)
                damaged = copy.deepcopy(row)
                damaged["episode_ledger"][0]["arm"] = "sequence_uniform"
                with self.assertRaises(AssertionError):
                    verify_ledger(damaged)
        finally:
            adapter.close()

    def test_early_discovery_has_exact_ledger_and_replay(self):
        from integrations.salon.adapter import Adapter
        from integrations.salon.model import Action
        from integrations.salon_ablation.experiment import replay
        from integrations.salon_portfolio.experiment import campaign
        from scripts.verify_salon_portfolio import verify_ledger
        adapter = Adapter("read_scope")
        try:
            row = campaign(adapter,"portfolio_balanced",91204,120)
            self.assertTrue(row["detected"])
            verify_ledger(row)
            self.assertEqual(replay(adapter,[Action(**s["action"]) for s in row["trace"]],"ANY"),row["trace"])
        finally:
            adapter.close()
