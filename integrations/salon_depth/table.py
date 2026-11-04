"""Transition tables recorded from the real HTTP/SQL backend.

Each table maps a concrete business state and one action of the finite campaign
domain to the observed HTTP response, the next state and the oracle verdict.
Only states reached through violation-free transitions are expanded, because
every campaign episode stops at its first oracle violation.
"""
from dataclasses import asdict
import json

from integrations.salon.model import ACTORS, OPERATIONS, RESOURCES, Action
from integrations.salon.oracle import check

ACTIONS = tuple(Action(o, a, r) for o in OPERATIONS for a in ACTORS for r in RESOURCES)
INDEX = {action: i for i, action in enumerate(ACTIONS)}

def state_key(snapshot):
    return json.dumps(snapshot, sort_keys=True, separators=(",", ":"))

def restore(database, snapshot):
    """Write a snapshot into a disposable research database."""
    with database.transaction() as conn:
        for table in ("ledger", "bookings", "slots", "users"):
            conn.execute("DELETE FROM " + table)
        for user, row in snapshot["users"].items():
            conn.execute("INSERT INTO users VALUES (?,?,?,?,?)",
                         (user, row["tenant"], row["role"], database._credentials[user], row["balance"]))
        for slot, row in snapshot["slots"].items():
            conn.execute("INSERT INTO slots VALUES (?,?,?,?,?,?)",
                         (slot, row["tenant"], row["service"], row["price"], row["capacity"], row["occupied"]))
        for booking, row in snapshot["bookings"].items():
            conn.execute("INSERT INTO bookings VALUES (?,?,?,?,?,?,?)",
                         (booking, row["tenant"], row["customer"], row["slot"], row["status"],
                          row["paid"], row["refunded"]))
        for entry in snapshot["ledger"]:
            conn.execute("INSERT INTO ledger(booking,customer,kind,amount) VALUES (?,?,?,?)",
                         (entry["booking"], entry["customer"], entry["kind"], entry["amount"]))

def explore(adapter, levels=7):
    """Record every action from each clean state reachable within `levels` actions."""
    adapter.reset()
    initial = adapter.snapshot()
    states, responses = [initial], []
    ids, response_ids = {state_key(initial): 0}, {}
    edges = {}
    frontier, queued = [0], {0}
    for _ in range(levels + 1):
        following = []
        for sid in frontier:
            row = []
            for action in ACTIONS:
                restore(adapter.database, states[sid])
                before = adapter.snapshot()
                if before != states[sid]:
                    raise AssertionError("state restoration is not exact")
                response = adapter.execute(action)
                after = adapter.snapshot()
                violations = check(before, action, response, after)
                key = state_key(after)
                if key not in ids:
                    ids[key] = len(states)
                    states.append(after)
                if not violations and ids[key] not in queued:
                    queued.add(ids[key])
                    following.append(ids[key])
                rkey = json.dumps(response, sort_keys=True, separators=(",", ":"))
                if rkey not in response_ids:
                    response_ids[rkey] = len(responses)
                    responses.append(response)
                row.append([ids[key], response_ids[rkey], violations])
            edges[sid] = row
        frontier = following
    return {"actions": [asdict(a) for a in ACTIONS], "states": states,
            "responses": responses, "edges": {str(k): v for k, v in edges.items()},
            "levels": levels}

_WORKER = {}

def _start_worker(variant):
    from integrations.salon.adapter import Adapter
    _WORKER["adapter"] = Adapter(variant)

def _expand(state):
    adapter, row = _WORKER["adapter"], []
    for action in ACTIONS:
        restore(adapter.database, state)
        before = adapter.snapshot()
        if before != state:
            raise AssertionError("state restoration is not exact")
        response = adapter.execute(action)
        after = adapter.snapshot()
        row.append((after, response, check(before, action, response, after)))
    return row

def explore_parallel(variant, levels=7, workers=8):
    """Same table as `explore`, expanding each breadth-first level across processes."""
    from multiprocessing import get_context
    from integrations.salon.adapter import Adapter
    adapter = Adapter(variant)
    adapter.reset()
    initial = adapter.snapshot()
    adapter.close()
    states, responses = [initial], []
    ids, response_ids = {state_key(initial): 0}, {}
    edges, frontier, queued = {}, [0], {0}
    with get_context("fork").Pool(workers, _start_worker, (variant,)) as pool:
        for _ in range(levels + 1):
            following = []
            rows = pool.map(_expand, [states[sid] for sid in frontier], chunksize=1)
            for sid, observed in zip(frontier, rows):
                row = []
                for after, response, violations in observed:
                    key = state_key(after)
                    if key not in ids:
                        ids[key] = len(states)
                        states.append(after)
                    if not violations and ids[key] not in queued:
                        queued.add(ids[key])
                        following.append(ids[key])
                    rkey = json.dumps(response, sort_keys=True, separators=(",", ":"))
                    if rkey not in response_ids:
                        response_ids[rkey] = len(responses)
                        responses.append(response)
                    row.append([ids[key], response_ids[rkey], violations])
                edges[sid] = row
            frontier = following
    return {"actions": [asdict(a) for a in ACTIONS], "states": states,
            "responses": responses, "edges": {str(k): v for k, v in edges.items()},
            "levels": levels}

class TableAdapter:
    """Adapter-compatible replay of a recorded table; unknown steps fall back to the backend."""

    def __init__(self, table, fallback=None):
        self.states, self.responses = table["states"], table["responses"]
        self.edges = {int(k): v for k, v in table["edges"].items()}
        self.ids = {state_key(s): i for i, s in enumerate(self.states)}
        self.fallback = fallback
        self.misses = 0
        self.current = 0

    def reset(self):
        self.current = 0

    def snapshot(self):
        return self.states[self.current]

    def execute(self, action):
        row = self.edges.get(self.current)
        if row is None:
            return self._miss(action)
        target, response, _ = row[INDEX[action]]
        self.current = target
        return self.responses[response]

    def _miss(self, action):
        if self.fallback is None:
            raise KeyError("state outside the recorded table")
        self.misses += 1
        restore(self.fallback.database, self.states[self.current])
        response = self.fallback.execute(action)
        after = self.fallback.snapshot()
        key = state_key(after)
        if key not in self.ids:
            self.ids[key] = len(self.states)
            self.states.append(after)
        self.current = self.ids[key]
        return response
