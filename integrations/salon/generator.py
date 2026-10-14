"""Generic bounded program mutations, independent of the specification."""
from dataclasses import replace
from .model import Action, ACTORS, OPERATIONS, RESOURCES

OPERATORS = ("field", "insert", "duplicate", "delete", "swap", "splice")

class Mutator:
    def __init__(self, rng, depth):
        self.rng, self.depth = rng, depth

    def random_action(self):
        return Action(self.rng.choice(OPERATIONS), self.rng.choice(ACTORS), self.rng.choice(RESOURCES))

    def mutate(self, source, donor, operator=None):
        sequence = list(source)
        operator = operator or self.rng.choice(OPERATORS)
        if not sequence or not donor or operator not in OPERATORS:
            raise ValueError("invalid mutation input")
        index = self.rng.randrange(len(sequence))
        if operator == "field":
            field = self.rng.choice(("operation", "actor", "resource"))
            domain = {"operation": OPERATIONS, "actor": ACTORS, "resource": RESOURCES}[field]
            sequence[index] = replace(sequence[index], **{field: self.rng.choice(domain)})
        elif operator == "insert":
            sequence.insert(index, self.random_action())
        elif operator == "duplicate":
            n = self.rng.randint(1, min(3, len(sequence)-index))
            sequence[index+n:index+n] = sequence[index:index+n]
        elif operator == "delete":
            if len(sequence) > 1:
                del sequence[index]
        elif operator == "swap":
            other = self.rng.randrange(len(sequence))
            sequence[index], sequence[other] = sequence[other], sequence[index]
        else:
            start = self.rng.randrange(len(donor))
            n = self.rng.randint(1, min(3, len(donor)-start))
            sequence[index:index] = donor[start:start+n]
        return sequence[:self.depth], operator
