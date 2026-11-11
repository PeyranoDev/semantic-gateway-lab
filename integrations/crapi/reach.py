"""Exact reach over the crAPI specification model (same table format as salon_depth)."""
import json

from integrations.salon_depth.model import Table
from .model import ACTIONS, SpecAdapter, violations

def explore(removed, target, levels=7):
    """Record every action from each state reachable without a `target` violation.

    crAPI has several defects at once, so crAPI campaigns stop an episode only at the
    target property. Non-target violations are recorded as ordinary transitions.
    """
    model = SpecAdapter(removed)
    model.reset()
    initial = model.snapshot()
    states, ids = [initial], {json.dumps(initial, sort_keys=True): 0}
    edges, frontier, queued = {}, [0], {0}
    for _ in range(levels + 1):
        following = []
        for sid in frontier:
            row = []
            for action in ACTIONS:
                model.restore(states[sid])
                before = model.snapshot()
                allowed = model.execute(action)["allowed"]
                after = model.snapshot()
                errors = [target] if target in violations(before, action, allowed, after) else []
                key = json.dumps(after, sort_keys=True)
                if key not in ids:
                    ids[key] = len(states)
                    states.append(after)
                if not errors and ids[key] not in queued:
                    queued.add(ids[key])
                    following.append(ids[key])
                row.append([ids[key], 0, errors])
            edges[str(sid)] = row
        frontier = following
    return Table({"edges": edges, "states": states}, actions=ACTIONS)
