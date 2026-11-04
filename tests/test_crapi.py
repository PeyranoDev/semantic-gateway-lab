"""crAPI specification model, exact reach and mutation enumeration (no live service)."""
from collections import Counter
from fractions import Fraction
import unittest

from integrations.crapi.generator import Mutator
from integrations.crapi.model import (ACTIONS, DOCUMENTED_DEFECTS, FIELDS, Action, SpecAdapter,
                                      initial_state, legitimate_seeds, violations)
from integrations.salon_depth.model import mutations

class _PathRng:
    def __init__(self, path):
        self.path, self.position, self.factors = path, 0, []

    def _pick(self, size):
        self.factors.append(size)
        value = self.path[self.position] if self.position < len(self.path) else 0
        self.position += 1
        return value

    def choice(self, values):
        return values[self._pick(len(values))]

    def randrange(self, stop):
        return self._pick(stop)

    def randint(self, low, high):
        return low + self._pick(high - low + 1)

def walked(source, donor):
    stack, out = [[]], Counter()
    while stack:
        path = stack.pop()
        rng = _PathRng(path)
        program, _ = Mutator(rng, 8).mutate(source, donor)
        if len(rng.factors) > len(path):
            stack.extend(path + [i] for i in range(rng.factors[len(path)]))
            continue
        p = Fraction(1)
        for size in rng.factors:
            p /= size
        out[tuple(program)] += p
    return out

def run(removed, program):
    model, seen = SpecAdapter(removed), []
    for action in program:
        before = model.snapshot()
        allowed = model.execute(action)["allowed"]
        seen.append(violations(before, action, allowed, model.snapshot()))
    return seen

class CrapiModelTest(unittest.TestCase):
    def test_domain_is_the_full_product(self):
        self.assertEqual(len(ACTIONS), 70)
        self.assertEqual(len(set(ACTIONS)), 70)

    def test_legitimate_tasks_are_clean_under_the_specification_and_hypothesis(self):
        for removed in (frozenset(), DOCUMENTED_DEFECTS):
            for program in legitimate_seeds():
                self.assertEqual([v for v in run(removed, program) if v], [])

    def test_documented_defects_produce_their_violations(self):
        buy, alice = Action("buy", "alice"), "alice#1"
        self.assertEqual(run(DOCUMENTED_DEFECTS, [Action("read_order", "alice", "other")]),
                         [["ORDER_PRIVACY"]])
        refund = run(DOCUMENTED_DEFECTS, [buy, Action("set_returned", "alice", alice)])[-1]
        self.assertIn("REFUND_WITHOUT_RETURN", refund)
        self.assertIn("ORDER_TAMPERING", refund)
        bigger = run(DOCUMENTED_DEFECTS, [buy, Action("set_quantity", "alice", alice),
                                          Action("set_returned", "alice", alice)])[-1]
        self.assertIn("REFUND_EXCEEDS_PAYMENT", bigger)
        self.assertEqual(run(frozenset(), [buy, Action("set_returned", "alice", alice)])[-1], [])

    def test_return_rules_hold_under_the_hypothesis(self):
        program = [Action("buy", "alice"), Action("request_return", "alice", "alice#1"),
                   Action("request_return", "alice", "alice#1"),
                   Action("request_return", "bob", "alice#1")]
        self.assertEqual([v for v in run(DOCUMENTED_DEFECTS, program) if v], [])
        self.assertEqual(initial_state()["credit"], {"alice": 100, "bob": 100})

    def test_mutation_enumeration_equals_every_choice_path(self):
        seeds = legitimate_seeds()
        for source, donor in ((seeds[0], seeds[1]), (seeds[1], seeds[5])):
            exact = Counter()
            for program, p in mutations(source, donor, 8, FIELDS, ACTIONS):
                exact[tuple(program)] += p
            self.assertEqual(walked(source, donor), exact)

if __name__ == "__main__":
    unittest.main()
