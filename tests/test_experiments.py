import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from fuzzlab.fuzzer import Campaign, replay
from fuzzlab.model import Action, STRATEGIES
from fuzzlab.report import summarize, wilson
from fuzzlab.analyze import distinguishability

def stable(result):
    return {k: v for k, v in result.items() if k not in ("elapsed_s", "gateway_p95_us")}

class ExperimentTests(unittest.TestCase):
    def test_bounded_abstraction_counterexample(self):
        result = distinguishability()
        witness = result["collisions"]["enabled"]
        self.assertIsNotNone(witness)
        self.assertIsNone(result["collisions"]["enriched"])
        outcomes = []
        from fuzzlab.backend import Gateway
        for key in ("first_prefix", "second_prefix"):
            g = Gateway()
            for a in witness[key]:
                g.execute(Action(**a))
            outcomes.append(g.execute(Action(**witness["distinguishing_action"]))["allowed"])
        self.assertNotEqual(*outcomes)

    def test_fixed_control_all_strategies(self):
        for strategy in STRATEGIES:
            with self.subTest(strategy=strategy):
                result = Campaign(strategy, budget=400, seed=7).run()
                self.assertFalse(result["detected"])
                self.assertEqual(result["calls"], 400)
                self.assertTrue(result["right_censored"])
                self.assertEqual(result["allowed"] + result["denied"], 400)

    def test_tiny_budget_all_strategies(self):
        for strategy in STRATEGIES:
            self.assertEqual(Campaign(strategy, budget=1).run()["calls"], 1)

    def test_determinism_all_strategies(self):
        for strategy in STRATEGIES:
            self.assertEqual(stable(Campaign(strategy, "wrong_recipient", budget=300, seed=3).run()),
                             stable(Campaign(strategy, "wrong_recipient", budget=300, seed=3).run()))

    def test_hash_seed_does_not_change_campaign(self):
        code = ('import json; from fuzzlab.fuzzer import Campaign; '
                'r=Campaign("enriched","wrong_recipient",seed=8,budget=200).run(); '
                'r.pop("elapsed_s"); r.pop("gateway_p95_us"); print(json.dumps(r,sort_keys=True))')
        outputs = [subprocess.check_output([sys.executable, "-c", code],
                   env={**os.environ, "PYTHONHASHSEED": seed}, text=True) for seed in ("1", "999")]
        self.assertEqual(outputs[0], outputs[1])

    def test_invalid_campaign_parameters(self):
        for kwargs in ({"budget": 0}, {"depth": 1}, {"strategy": "unknown"}, {"mutant": "unknown"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Campaign(**kwargs).run()

    def test_detected_witness_replays(self):
        result = Campaign("enriched", "cross_department_read", seed=0, budget=200).run()
        self.assertTrue(result["detected"])
        actions = [Action(**a) for a in result["minimal_trace"]]
        self.assertIn(result["violations"][0], replay(actions, result["mutant"])["violations"])
        self.assertEqual(replay(actions)["violations"], [])
        self.assertLessEqual(result["first_failure_call"], result["budget"])

    def test_censored_summary_does_not_drop_misses(self):
        hit = Campaign("random", "cross_department_read", seed=0, budget=50).run()
        self.assertTrue(hit["detected"])
        miss = dict(hit, detected=False, first_failure_call=None, calls=50)
        summary = summarize([hit, miss])[0]
        self.assertEqual(summary["rate"], .5)
        self.assertEqual(summary["mean_capped_calls"], (hit["first_failure_call"] + 50)/2)

    def test_wilson_interval_nonzero_uncertainty(self):
        low, high = wilson(0, 10)
        self.assertAlmostEqual(low, 0)
        self.assertGreater(high, .2)
        low, high = wilson(10, 10)
        self.assertLess(low, .8)
        self.assertAlmostEqual(high, 1)

    def test_cli_artifacts_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "config.json"
            config.write_text(json.dumps(dict(seeds=[0], strategies=["random"],
                               mutants=["fixed", "cross_department_read"], budget=40, depth=8)))
            command = [sys.executable, "-m", "fuzzlab", "run", "--config", str(config), "--out", str(root / "out")]
            subprocess.run(command, check=True, capture_output=True)
            for file in ("manifest.json", "raw.jsonl", "summary.csv", "summary.md"):
                self.assertTrue((root / "out" / file).is_file())
            rows = [json.loads(line) for line in (root / "out/raw.jsonl").read_text().splitlines()]
            self.assertEqual(len(rows), 2)
            failed = subprocess.run(command, capture_output=True)
            self.assertNotEqual(failed.returncode, 0)
