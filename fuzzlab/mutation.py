"""Generic sequence mutations over legitimate programs; no defect labels or oracle."""
from dataclasses import replace
from .abstraction import DOCUMENT_IDS
from .model import Action, TOOLS, fixture_approval, initial_state, token_pool

OPERATORS = ("field", "insert", "duplicate", "delete", "swap", "splice")

def legitimate_seeds():
    state = initial_state()
    programs = []
    for identifier, document in sorted(state.documents.items()):
        actor = document.owner
        recipients = [name for name, principal in sorted(state.principals.items())
                      if principal.department == document.department and name != actor]
        if recipients:
            target = recipients[0]
            programs.append([Action("initiate_share", actor, identifier, target),
                             Action("accept_share", target, identifier),
                             Action("read_document", target, identifier),
                             Action("revoke_share", actor, identifier)])
        # Two approved lifecycle transactions, each with a distinct fresh nonce.
        first = fixture_approval(identifier, actor, identifier + "-first")
        second = fixture_approval(identifier, actor, identifier + "-second")
        programs.append([Action("request_delete", actor, identifier),
                         Action("delete_document", actor, identifier, token=first),
                         Action("create_document", actor, identifier),
                         Action("request_delete", actor, identifier),
                         Action("delete_document", actor, identifier, token=second)])
    programs.append([Action("list_documents"), Action("read_document"),
                     Action("update_document"), Action("export_document")])
    return programs

class SequenceMutator:
    def __init__(self, rng, depth=20):
        self.rng, self.depth = rng, depth
        self.actors = tuple(sorted(initial_state().principals))
        self.tokens = tuple(dict.fromkeys((*token_pool(),
            *(a.token for program in legitimate_seeds() for a in program if a.token))))

    def _random_action(self, anchor, program):
        tokens = tuple(dict.fromkeys(a.token for a in program if a.token))
        token_choices = tokens if tokens and self.rng.random() < .7 else self.tokens
        return Action(self.rng.choice(TOOLS), anchor.actor, anchor.document,
                      self.rng.choice(self.actors), token=self.rng.choice(token_choices))

    def mutate(self, source, donor, operator=None):
        if not source or not donor:
            raise ValueError("mutation requires nonempty source and donor")
        sequence = list(source)
        operator = operator or self.rng.choice(OPERATORS)
        if operator not in OPERATORS:
            raise ValueError("unknown mutation")
        index = self.rng.randrange(len(sequence))
        anchor = sequence[index]
        if operator == "field":
            field = self.rng.choice(("actor", "document", "target", "token", "content"))
            domain = {"actor": self.actors, "document": DOCUMENT_IDS,
                      "target": self.actors, "token": self.tokens,
                      "content": ("updated", "replacement", "confidential")}[field]
            observed = tuple(dict.fromkeys(getattr(a, field) for a in sequence
                                           if getattr(a, field) != ""))
            choices = observed if observed and self.rng.random() < .7 else domain
            sequence[index] = replace(anchor, **{field: self.rng.choice(choices)})
        elif operator == "insert":
            sequence.insert(index, self._random_action(anchor, sequence))
        elif operator == "duplicate":
            length = self.rng.randint(1, min(3, len(sequence) - index))
            segment = sequence[index:index + length]
            sequence[index + length:index + length] = segment
        elif operator == "delete":
            if len(sequence) > 1:
                del sequence[index]
        elif operator == "swap":
            other = self.rng.randrange(len(sequence))
            sequence[index], sequence[other] = sequence[other], sequence[index]
        elif operator == "splice":
            start = self.rng.randrange(len(donor))
            length = self.rng.randint(1, min(3, len(donor) - start))
            sequence[index:index] = donor[start:start + length]
        return sequence[:self.depth], operator
