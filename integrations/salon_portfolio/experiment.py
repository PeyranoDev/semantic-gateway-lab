"""Shared ANY-property oracle and strict per-campaign request accounting."""
from collections import Counter
from dataclasses import asdict
import time
from integrations.salon.feedback import canonical
from integrations.salon.oracle import check
from integrations.salon.model import Action
from integrations.salon_ablation.experiment import minimize, replay
from integrations.salon_ablation.programs import bank_digest
from .programs import Scheduler


def campaign(adapter, mode, seed, budget, depth=8):
    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 1:
        raise ValueError("positive integer budget required")
    started = time.perf_counter()
    scheduler = Scheduler(mode, seed, depth)
    calls = bootstrap_calls = 0
    witness, ledger = [], []
    observed, operators = set(), Counter()
    while calls < budget and not witness:
        arm, program, bootstrap, operator = scheduler.next()
        if not bootstrap and arm != "random":
            operators[operator] += 1
        adapter.reset()
        trace = []
        for action in program[:budget-calls]:
            before = adapter.snapshot()
            response = adapter.execute(action)
            after = adapter.snapshot()
            errors = check(before, action, response, after)
            calls += 1
            bootstrap_calls += int(bootstrap)
            observed.update((canonical(before), canonical(after)))
            trace.append({"action": asdict(action), "response": response,
                          "before": before, "after": after, "violations": errors})
            if errors:
                witness = trace
                break
        scheduler.charge(arm, len(trace))
        ledger.append({"arm":arm, "calls":len(trace), "bootstrap":bootstrap, "operator":operator})
    minimal_trace, shrink_calls = [], 0
    if witness:
        minimal, shrink_calls = minimize(adapter, [Action(**s["action"]) for s in witness], "ANY")
        minimal_trace = replay(adapter, minimal, "ANY")
        assert minimal_trace[-1]["violations"]
    return {"mode":mode, "target":"ANY", "seed":seed, "budget":budget, "depth":depth,
            "calls":calls, "detected":bool(witness), "right_censored":not witness,
            "episodes":len(ledger), "bootstrap_calls":bootstrap_calls,
            "observed_states":len(observed), "corpus_entries":0, "corpus_evictions":0,
            "operators":dict(operators), "other_errors":{}, "trace":witness,
            "minimal_trace":minimal_trace, "shrink_calls":shrink_calls,
            "elapsed_s":time.perf_counter()-started, "initial_bank_sha256":bank_digest(scheduler.bank),
            "arm_calls":scheduler.calls, "episode_ledger":ledger}
