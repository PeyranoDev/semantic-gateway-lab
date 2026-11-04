"""Exact reachability model: enumeration, dynamic programming and BFS depth."""
from collections import Counter
from fractions import Fraction
import random
import unittest

from integrations.salon.generator import Mutator
from integrations.salon.model import Action, legitimate_seeds
from integrations.salon_depth.model import (Table, detection_curve, mutation_episode, mutations,
                                            random_episode, run_program, shortest_witness, summary)
from integrations.salon_depth.table import ACTIONS, INDEX

def synthetic(rule):
    """One-state-per-step table: rule(state, action) -> (next_state, violations)."""
    edges, states, frontier = {}, [0], [0]
    while frontier:
        state = frontier.pop()
        row = []
        for action in ACTIONS:
            successor, violations = rule(state, action)
            if successor not in states:
                states.append(successor)
                if not violations and successor < 10:
                    frontier.append(successor)
            row.append([states.index(successor), 0, list(violations)])
        edges[str(states.index(state))] = row
    return Table({"edges": edges, "states": states})

TRIGGER = Action("refund", "staff_a", "a")
OTHER = Action("pay", "alice", "a")

def two_step(state, action):
    """Violation only on TRIGGER after OTHER; other actions keep the state."""
    if state == 0 and action == OTHER:
        return 1, ()
    if state == 1 and action == TRIGGER:
        return 2, ("REFUND_REPLAY",)
    return state, ()

class _PathRng:
    """Deterministic RNG that follows a prefix of choices and records branching factors."""

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

def _all_choice_paths(source, donor):
    stack, out = [[]], []
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
        out.append((program, p))
    return out

class DepthModelTest(unittest.TestCase):
    def test_shortest_witness_counts_distinct_shortest_sequences(self):
        depth, witness, count = shortest_witness(synthetic(two_step), "REFUND_REPLAY")
        self.assertEqual((depth, witness, count), (2, [OTHER, TRIGGER], 1))
        self.assertEqual(shortest_witness(synthetic(two_step), "SLOT_CAPACITY")[0], None)

    def test_run_program_stops_at_first_violation(self):
        table = synthetic(two_step)
        self.assertEqual(run_program(table, [OTHER, TRIGGER, OTHER], "REFUND_REPLAY"), (2, True))
        self.assertEqual(run_program(table, [OTHER, TRIGGER], "SLOT_CAPACITY"), (2, False))
        self.assertEqual(run_program(table, [TRIGGER, OTHER], "REFUND_REPLAY"), (2, False))

    def test_random_episode_is_a_probability_distribution(self):
        episode = random_episode(synthetic(two_step), "REFUND_REPLAY", depth=3)
        self.assertEqual(sum(episode.detect) + sum(episode.stop), 1)
        n = Fraction(1, len(ACTIONS))
        # Lengths 2 and 3: OTHER then TRIGGER at calls (1,2) or (2,3) or (1,3);
        # in state 1 every action except TRIGGER keeps the state.
        expected = (Fraction(1, 3) * n * n
                    + Fraction(1, 3) * (n * n + (1 - n) * n * n + n * (1 - n) * n))
        self.assertEqual(episode.probability(), expected)

    def test_mutation_enumeration_equals_every_mutator_choice_path(self):
        """Exhaustively drive Mutator.mutate through every random choice path."""
        for source, donor in ((legitimate_seeds()[0], legitimate_seeds()[3]),
                              (legitimate_seeds()[1], legitimate_seeds()[2]),
                              ([Action("pay", "bob", "b")], legitimate_seeds()[1])):
            exact = Counter()
            for program, p in mutations(source, donor):
                exact[tuple(program)] += p
            walked = Counter()
            for program, p in _all_choice_paths(source, donor):
                walked[tuple(program)] += p
            self.assertEqual(sum(exact.values()), 1)
            self.assertEqual(walked, exact)

    def test_mutation_episode_uses_uniform_source_and_donor(self):
        table = synthetic(two_step)
        bank = [[OTHER], [TRIGGER]]
        episode = mutation_episode(table, "REFUND_REPLAY", bank, depth=8)
        self.assertEqual(sum(episode.detect) + sum(episode.stop), 1)
        self.assertGreater(episode.probability(), 0)

    def test_detection_curve_is_geometric_for_single_call_episodes(self):
        table = synthetic(lambda s, a: (1, ("X",)) if a == TRIGGER else (s, ()))
        episode = random_episode(table, "X", depth=1)
        p = 1 / len(ACTIONS)
        detected, capped = summary(detection_curve(episode, 50), 50)
        self.assertAlmostEqual(detected, 1 - (1 - p) ** 50)
        self.assertAlmostEqual(capped, sum((1 - p) ** t for t in range(50)))

    def test_detection_curve_charges_the_prefix(self):
        table = synthetic(lambda s, a: (1, ("X",)) if a == TRIGGER else (s, ()))
        episode = random_episode(table, "X", depth=1)
        first = detection_curve(episode, 10, prefix=[(4, False), (4, False)])
        self.assertEqual(sum(first[:9]), 0)
        self.assertEqual(detection_curve(episode, 10, prefix=[(3, True)])[3], 1.0)

    def test_action_index_is_a_bijection(self):
        self.assertEqual(len(ACTIONS), 175)
        self.assertEqual(sorted(INDEX.values()), list(range(175)))

if __name__ == "__main__":
    unittest.main()

class PairedStatsTest(unittest.TestCase):
    def test_mcnemar_exact_matches_binomial_tails(self):
        from integrations.salon_depth.stats import mcnemar_exact
        self.assertEqual(mcnemar_exact(0, 0), 1.0)
        self.assertAlmostEqual(mcnemar_exact(0, 6), 2 / 64)
        self.assertAlmostEqual(mcnemar_exact(1, 9), 2 * 11 / 1024)
        self.assertEqual(mcnemar_exact(5, 5), 1.0)

    def test_a12_extremes_and_ties(self):
        from integrations.salon_depth.stats import a12
        self.assertEqual(a12([5, 6], [1, 2]), 1.0)
        self.assertEqual(a12([1, 2], [5, 6]), 0.0)
        self.assertEqual(a12([3, 3], [3, 3]), 0.5)
        with self.assertRaises(ValueError):
            a12([], [1])

    def test_holm_is_monotone_and_capped(self):
        from integrations.salon_depth.stats import holm
        self.assertEqual(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
        self.assertEqual(holm([0.5, 0.9]), [1.0, 1.0])

try:
    import fastapi, httpx  # noqa: F401
    HAS_HTTP = True
except ImportError:
    HAS_HTTP = False

@unittest.skipUnless(HAS_HTTP, "install backends/salon/requirements.lock")
class RecordedTableTest(unittest.TestCase):
    def test_parallel_exploration_equals_sequential_and_replays(self):
        from integrations.salon.adapter import Adapter
        from integrations.salon_depth.table import TableAdapter, explore, explore_parallel
        adapter = Adapter("refund_replay")
        try:
            sequential = explore(adapter, levels=1)
        finally:
            adapter.close()
        self.assertEqual(explore_parallel("refund_replay", levels=1, workers=2), sequential)
        replay = TableAdapter(sequential)
        replay.reset()
        for action in legitimate_seeds()[1][:2]:  # reserve, pay: within two levels
            replay.execute(action)
        booking = replay.snapshot()["bookings"]["a"]
        self.assertEqual((booking["status"], booking["paid"]), ("reserved", 1000))
        with self.assertRaises(KeyError):
            replay.execute(legitimate_seeds()[1][2])
