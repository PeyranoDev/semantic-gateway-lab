"""Verify treatment separation and exact preservation of the four original engines."""
import ast
from pathlib import Path
import random
import unittest

from fuzzlab.feedback import Corpus
from integrations.salon.generator import Mutator
from integrations.salon.model import legitimate_seeds
from integrations.salon_ablation.analysis import effects, CONTRASTS
from integrations.salon_ablation.programs import MODES, bank, bank_digest, next_program

try:
    import fastapi, httpx
    HAS_HTTP = True
except ImportError:
    HAS_HTTP = False

class AblationPortableTests(unittest.TestCase):
    def test_random_bank_matches_legitimate_bank_shape_and_is_reproducible(self):
        one = bank("mutation_unseeded",600)
        self.assertEqual(one,bank("mutation_unseeded",600))
        self.assertNotEqual(one,bank("mutation_unseeded",601))
        self.assertEqual(list(map(len,one)),list(map(len,legitimate_seeds())))
        self.assertNotEqual(one,legitimate_seeds())
        self.assertEqual(bank_digest(one),bank_digest(bank("mutation_unseeded",600)))

    def test_selection_has_no_oracle_or_backend_dependency(self):
        path = Path(__file__).parents[1]/"integrations/salon_ablation/programs.py"
        imports = [n.module for n in ast.walk(ast.parse(path.read_text())) if isinstance(n,ast.ImportFrom)]
        self.assertFalse(any("oracle" in name or "backend" in name for name in imports))
        self.assertNotIn("VARIANT_TARGET",path.read_text())

    def test_append_preserves_a_whole_valid_prefix(self):
        programs = legitimate_seeds()
        rng = random.Random(19)
        for _ in range(30):
            program,operator = next_program("seed_extend",programs,Corpus(64),rng,Mutator(rng,8),8)
            self.assertEqual(operator,"append")
            self.assertTrue(any(program[:len(seed)] == seed and len(program)>len(seed) for seed in programs))
            self.assertLessEqual(len(program),8)

    def test_replay_never_changes_a_seed(self):
        programs = legitimate_seeds()
        rng = random.Random(21)
        for _ in range(20):
            program,operator = next_program("seed_replay",programs,Corpus(64),rng,Mutator(rng,8),8)
            self.assertIn(program,programs)
            self.assertEqual(operator,"replay")

    def test_paired_bootstrap_preserves_constant_effects(self):
        rows = [{"variant":"read_scope","target":"BOOKING_SCOPE","mode":mode,"seed":seed,
                 "calls":10+index,"detected":True}
                for seed in range(3) for index,mode in enumerate(MODES)]
        result = effects(rows,samples=20)
        self.assertEqual(len(result),len(CONTRASTS))
        for entry in result:
            difference = MODES.index(entry["right"])-MODES.index(entry["left"])
            self.assertEqual(entry["mean_right_minus_left_capped_calls"],difference)
            self.assertEqual(entry["paired_bootstrap95_capped_calls"],[difference,difference])
            self.assertEqual(entry["paired_bootstrap95_detection_difference"],[0,0])

@unittest.skipUnless(HAS_HTTP,"install backends/salon/requirements.lock")
class AblationHTTPTests(unittest.TestCase):
    def setUp(self):
        from integrations.salon.adapter import Adapter
        self.adapter = Adapter()

    def tearDown(self):
        self.adapter.close()

    def test_original_modes_remain_exactly_equivalent(self):
        from integrations.salon.experiment import campaign as original
        from integrations.salon_ablation.experiment import campaign
        for mode in ("random","sequence_uniform","sequence_enabled","sequence_enriched"):
            old = original(self.adapter,mode,"BOOKING_SCOPE",87123,45)
            new = campaign(self.adapter,mode,"BOOKING_SCOPE",87123,45)
            old.pop("elapsed_s")
            new.pop("elapsed_s")
            new.pop("initial_bank_sha256")
            self.assertEqual(old,new,mode)

    def test_fixed_any_control_observes_all_properties(self):
        from integrations.salon_ablation.experiment import campaign
        for mode in MODES:
            row = campaign(self.adapter,mode,"ANY",87124,36)
            self.assertFalse(row["detected"])
            self.assertFalse(row["other_errors"])
            self.assertEqual(row["calls"],36)

    def test_charged_warmup_is_identical_before_generation(self):
        from integrations.salon_ablation.experiment import campaign
        warmup = campaign(self.adapter,"random_bootstrap","BOOKING_SCOPE",87125,10)
        mutation = campaign(self.adapter,"sequence_uniform","BOOKING_SCOPE",87125,10)
        for key in ("calls","bootstrap_calls","episodes","observed_states","operators"):
            self.assertEqual(warmup[key],mutation[key])
        self.assertEqual(warmup["bootstrap_calls"],10)

if __name__ == "__main__":
    unittest.main()
