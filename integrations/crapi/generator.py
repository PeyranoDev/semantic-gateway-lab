"""Generic bounded program mutations over the crAPI domain (same semantics as the salon Mutator)."""
from dataclasses import replace

from .model import ACTIONS, FIELDS

OPERATORS = ("field", "insert", "duplicate", "delete", "swap", "splice")

class Mutator:
    def __init__(self, rng, depth):
        self.rng, self.depth = rng, depth

    def random_action(self):
        return self.rng.choice(ACTIONS)

    def mutate(self, source, donor):
        sequence = list(source)
        operator = self.rng.choice(OPERATORS)
        if not sequence or not donor:
            raise ValueError("invalid mutation input")
        index = self.rng.randrange(len(sequence))
        if operator == "field":
            field = self.rng.choice(tuple(FIELDS))
            sequence[index] = replace(sequence[index], **{field: self.rng.choice(FIELDS[field])})
        elif operator == "insert":
            sequence.insert(index, self.random_action())
        elif operator == "duplicate":
            n = self.rng.randint(1, min(3, len(sequence) - index))
            sequence[index + n:index + n] = sequence[index:index + n]
        elif operator == "delete":
            if len(sequence) > 1:
                del sequence[index]
        elif operator == "swap":
            other = self.rng.randrange(len(sequence))
            sequence[index], sequence[other] = sequence[other], sequence[index]
        else:
            start = self.rng.randrange(len(donor))
            n = self.rng.randint(1, min(3, len(donor) - start))
            sequence[index:index] = donor[start:start + n]
        return sequence[:self.depth], operator
