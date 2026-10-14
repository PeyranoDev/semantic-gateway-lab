"""Budgeted stateful testing against actual backend effects."""
from collections import Counter
from dataclasses import asdict
import hashlib
import math
import random
import time
from .abstraction import DOCUMENT_IDS, abstract, concrete_key, enabled_tools
from .backend import Gateway
from .model import Action, STRATEGIES, TOOLS, canonical, token_pool
from .oracle import inspect

def replay(actions, mutant="fixed"):
    gateway = Gateway(mutant)
    for index, action in enumerate(actions, 1):
        before = gateway.state.snapshot()
        response = gateway.execute(action)
        after = gateway.state.snapshot()
        failures = inspect(before, action, response, after)
        if failures:
            return {"step": index, "violations": failures, "response": response,
                    "before": before, "after": after}
    return {"step": None, "violations": []}

def minimize(actions, mutant, violation):
    """Deletion-based 1-minimal trace; not globally shortest. Separate budget."""
    candidate = list(actions)
    calls = 0
    changed = True
    while changed:
        changed = False
        for index in range(len(candidate)):
            trial = candidate[:index] + candidate[index + 1:]
            observed = replay(trial, mutant)
            calls += observed["step"] or len(trial)
            if violation in observed["violations"]:
                candidate = trial
                changed = True
                break
    return candidate, calls

class Campaign:
    def __init__(self, strategy="random", mutant="fixed", seed=0, budget=1500, depth=12):
        if strategy not in STRATEGIES or budget <= 0 or depth < 2:
            raise ValueError("invalid campaign parameters")
        self.strategy, self.mutant, self.seed = strategy, mutant, seed
        self.budget, self.depth = budget, depth
        self.rng = random.Random(seed)

    def _action(self, snapshot):
        if self.strategy == "random" or self.rng.random() >= 0.8:
            tool = self.rng.choice(TOOLS)
        else:
            tool = self.rng.choice(enabled_tools(snapshot))
        # Identical parameter generator for all strategies; no valid-argument oracle.
        return Action(tool, self.rng.choice(tuple(sorted(snapshot["principals"]))),
                      self.rng.choice(DOCUMENT_IDS),
                      self.rng.choice(tuple(sorted(snapshot["principals"]))),
                      token=self.rng.choice(token_pool()))

    def run(self):
        started = time.perf_counter()
        corpus, visits = {}, Counter()
        business_states, edges = set(), set()
        abstract_edges = set()
        latencies = []
        spent = replay_calls = denied = allowed = episodes = 0
        first_step, trace, failure, witness = None, [], [], None
        initial = Gateway(self.mutant).state.snapshot()
        business_states.add(concrete_key(initial))
        if self.strategy != "random":
            corpus[abstract(initial, self.strategy)] = []
        while spent < self.budget and not failure:
            gateway = Gateway(self.mutant)
            prefix = []
            episodes += 1
            if corpus and self.rng.random() < 0.8:
                eligible = [key for key in sorted(corpus)
                            if len(corpus[key]) < min(self.depth, self.budget - spent)]
                if eligible:
                    key = self.rng.choices(eligible, weights=[1 / (1 + visits[k]) for k in eligible])[0]
                    visits[key] += 1
                    prefix = corpus[key]
            sequence = []
            for offset in range(self.depth):
                if spent >= self.budget:
                    break
                before = gateway.state.snapshot()
                is_replay = offset < len(prefix)
                action = prefix[offset] if is_replay else self._action(before)
                t0 = time.perf_counter_ns()
                response = gateway.execute(action)
                latencies.append(time.perf_counter_ns() - t0)
                after = gateway.state.snapshot()
                spent += 1
                replay_calls += int(is_replay)
                allowed += int(response["allowed"])
                denied += int(not response["allowed"])
                sequence.append(action)
                old, new = concrete_key(before), concrete_key(after)
                business_states.add(new)
                edges.add((old, action.tool, response["allowed"], new))
                if self.strategy != "random":
                    prior, key = abstract(before, self.strategy), abstract(after, self.strategy)
                    abstract_edges.add((prior, action.tool, response["allowed"], key))
                failure = inspect(before, action, response, after)
                if failure:
                    first_step, trace = spent, list(sequence)
                    witness = {"before": before, "after": after, "response": response}
                    break
                if self.strategy != "random" and len(sequence) < self.depth:
                    if key not in corpus or len(sequence) < len(corpus[key]):
                        corpus[key] = list(sequence)
        elapsed = time.perf_counter() - started
        shrunk, shrink_calls = minimize(trace, self.mutant, failure[0]) if failure else ([], 0)
        sorted_latency = sorted(latencies)
        p95 = sorted_latency[max(0, math.ceil(len(sorted_latency) * .95) - 1)] / 1000
        return {"strategy": self.strategy, "mutant": self.mutant, "seed": self.seed,
                "budget": self.budget, "max_depth": self.depth, "calls": spent,
                "replay_calls": replay_calls, "episodes": episodes, "allowed": allowed,
                "denied": denied, "detected": bool(failure), "first_failure_call": first_step,
                "right_censored": not bool(failure), "violations": failure,
                "elapsed_s": elapsed, "gateway_p95_us": p95,
                "concrete_states": len(business_states), "concrete_edges": len(edges),
                "abstract_states": len(corpus), "abstract_edges": len(abstract_edges),
                "trace": [asdict(a) for a in trace],
                "minimal_trace": [asdict(a) for a in shrunk], "witness": witness,
                "shrink_calls": shrink_calls,
                "coverage_digest": hashlib.sha256(canonical(sorted(edges)).encode()).hexdigest()}
