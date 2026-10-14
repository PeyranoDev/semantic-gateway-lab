"""Relational feedback and bounded corpus; authorization is never inferred here."""
from dataclasses import asdict
from .abstraction import DOCUMENT_IDS, abstract, enabled_tools
from .model import canonical

MODES = ("enabled", "enriched", "no_recipient", "no_approval", "no_owner")

def project(state, mode):
    if mode in ("enabled", "enriched"):
        return abstract(state, mode)
    if mode not in MODES:
        raise ValueError("unknown projection")
    documents = []
    for identifier in DOCUMENT_IDS:
        d = state["documents"].get(identifier)
        if d is None:
            documents.append(None)
            continue
        relations = []
        for actor, principal in sorted(state["principals"].items()):
            values = [principal["department"] == d["department"]]
            if mode != "no_owner":
                values.append(actor == d["owner"])
            if mode != "no_recipient":
                values.append(actor == d["pending"])
            values.append(actor in d["acl"])
            relations.append(values)
        documents.append((d["phase"], d["delete_requested"], relations))
    key = [enabled_tools(state), documents]
    if mode != "no_approval":
        key.append(sorted(state["used_nonces"]))
    return canonical(key)

def program_key(program):
    return canonical([asdict(a) for a in program])

class Corpus:
    def __init__(self, capacity=64, scheduler="rare"):
        if capacity < 1 or scheduler not in ("rare", "uniform"):
            raise ValueError("invalid corpus settings")
        self.capacity, self.scheduler = capacity, scheduler
        self.entries, self.visits = {}, {}
        self.evictions = 0

    def remember(self, key, program):
        current = self.entries.get(key)
        if current is not None:
            if (len(program), program_key(program)) < (len(current), program_key(current)):
                self.entries[key] = list(program)
            return
        if len(self.entries) >= self.capacity:
            victim = next(iter(self.entries))
            del self.entries[victim]
            self.visits.pop(victim, None)
            self.evictions += 1
        self.entries[key] = list(program)
        self.visits[key] = 0

    def select(self, rng):
        keys = sorted(self.entries)
        if not keys:
            raise ValueError("empty corpus")
        weights = ([1 / (1 + self.visits[key]) for key in keys]
                   if self.scheduler == "rare" else [1] * len(keys))
        key = rng.choices(keys, weights=weights)[0]
        self.visits[key] += 1
        return list(self.entries[key])
