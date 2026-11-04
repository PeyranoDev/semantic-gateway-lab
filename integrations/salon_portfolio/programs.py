"""Only call counts determine scheduling; no policy, response or mutant input."""
import random
from integrations.salon.generator import Mutator
from integrations.salon.model import legitimate_seeds

MODES = ("random", "sequence_uniform", "portfolio_balanced")
ARMS = MODES[:2]

class Scheduler:
    def __init__(self, mode, seed, depth=8):
        if mode not in MODES or depth < 5:
            raise ValueError("invalid scheduler")
        self.mode, self.depth = mode, depth
        # Isolated RNGs retain exactly the standalone component streams.
        self.rng = {arm: random.Random(seed) for arm in ARMS}
        self.mutator = {arm: Mutator(self.rng[arm], depth) for arm in ARMS}
        self.calls = dict.fromkeys(ARMS, 0)
        self.bank = legitimate_seeds()
        self.seed_index = 0

    def next(self):
        arm = (min(ARMS, key=self.calls.get)
               if self.mode == "portfolio_balanced" else self.mode)
        rng, mutate = self.rng[arm], self.mutator[arm]
        if arm == "random":
            return arm, [mutate.random_action() for _ in range(rng.randint(1, self.depth))], False, "random"
        if self.seed_index < len(self.bank):
            program = self.bank[self.seed_index]
            self.seed_index += 1
            return arm, list(program), True, "bootstrap"
        program, operator = mutate.mutate(rng.choice(self.bank), rng.choice(self.bank))
        return arm, program, False, operator

    def charge(self, arm, calls):
        if arm not in ARMS or not isinstance(calls, int) or isinstance(calls, bool) or not 1 <= calls <= self.depth:
            raise ValueError("invalid charged episode")
        self.calls[arm] += calls
