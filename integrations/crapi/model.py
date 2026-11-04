"""Finite crAPI shop domain and specification model (docs/crapi-protocol.md).

No crAPI imports. Orders are symbolic: `<actor>#<k>` is the actor's k-th order created
within the program, and `other` is a pre-seeded order of another account.
"""
from copy import deepcopy
from dataclasses import dataclass

ACTORS = ("alice", "bob")
OPERATIONS = ("buy", "list_orders", "read_order", "set_returned", "set_delivered",
              "set_quantity", "request_return")
TARGETS = ("alice#1", "alice#2", "bob#1", "bob#2", "other")
PRICE, CREDIT = 10, 100
PROPERTIES = ("ORDER_PRIVACY", "ORDER_TAMPERING", "REFUND_WITHOUT_RETURN",
              "REFUND_EXCEEDS_PAYMENT", "RETURN_RULES")

@dataclass(frozen=True)
class Action:
    operation: str
    actor: str = "alice"
    target: str = "alice#1"

    def __post_init__(self):
        if self.operation not in OPERATIONS or self.actor not in ACTORS or self.target not in TARGETS:
            raise ValueError("unknown operation, actor or target")

# Full product, as the generic mutator can set any field; buy/list ignore the target.
ACTIONS = tuple(Action(o, a, t) for o in OPERATIONS for a in ACTORS for t in TARGETS)
FIELDS = {"operation": OPERATIONS, "actor": ACTORS, "target": TARGETS}

def initial_state():
    return {"credit": {a: CREDIT for a in ACTORS}, "count": {a: 0 for a in ACTORS},
            "orders": {"other": {"owner": "other", "quantity": 1, "paid": PRICE,
                                 "status": "delivered", "refunded": 0}}}

def legitimate_seeds():
    """Valid customer tasks: purchase and review, purchase and return request."""
    programs = []
    for actor in ACTORS:
        first = actor + "#1"
        programs += [[Action("buy", actor, "alice#1"), Action("list_orders", actor, "alice#1"),
                      Action("read_order", actor, first)],
                     [Action("buy", actor, "alice#1"), Action("request_return", actor, first)],
                     [Action("buy", actor, "alice#1"), Action("buy", actor, "alice#1"),
                      Action("read_order", actor, actor + "#2")]]
    return programs

# Guards of the intended specification. A hypothesis removes a subset of them.
GUARDS = ("read_owner", "edit_status_denied", "edit_quantity_denied",
          "return_owner", "return_delivered", "buy_credit")
DOCUMENTED_DEFECTS = frozenset({"read_owner", "edit_status_denied", "edit_quantity_denied"})

def expected(state, action, removed=frozenset()):
    """Return (allowed, after) under the specification with `removed` guards disabled.

    Edits that the specification forbids are given their natural effect when a guard is
    removed: `returned` refunds quantity x price, and quantity edits change the quantity.
    """
    after = deepcopy(state)
    actor, op, key = action.actor, action.operation, action.target
    if op == "buy":
        if "buy_credit" not in removed and state["credit"][actor] < PRICE:
            return False, after
        after["count"][actor] += 1
        after["credit"][actor] -= PRICE
        after["orders"][f"{actor}#{after['count'][actor]}"] = {
            "owner": actor, "quantity": 1, "paid": PRICE, "status": "delivered", "refunded": 0}
        return True, after
    if op == "list_orders":
        return True, after
    order = state["orders"].get(key)
    if order is None:
        return False, after
    owner = order["owner"] == actor
    if op == "read_order":
        return owner or "read_owner" in removed, after
    if op in ("set_returned", "set_delivered"):
        if "edit_status_denied" not in removed or not owner:
            return False, after
        status = "returned" if op == "set_returned" else "delivered"
        target = after["orders"][key]
        if status != order["status"]:
            target["status"] = status
            if status == "returned":
                amount = order["quantity"] * PRICE
                after["credit"][actor] += amount
                target["refunded"] += amount
        return True, after
    if op == "set_quantity":
        if "edit_quantity_denied" not in removed or not owner:
            return False, after
        after["orders"][key]["quantity"] = 2
        return True, after
    if op == "request_return":
        if not owner and "return_owner" not in removed:
            return False, after
        if order["status"] != "delivered" and "return_delivered" not in removed:
            return False, after
        after["orders"][key]["status"] = "return pending"
        return True, after
    raise ValueError(op)

def violations(before, action, allowed, after):
    """Oracle: compare an observed transition with the intended specification."""
    intended_allowed, intended = expected(before, action)
    errors = []
    if action.operation == "read_order" and allowed and not intended_allowed:
        errors.append("ORDER_PRIVACY")
    for key, order in after["orders"].items():
        prior = before["orders"].get(key)
        if prior is None:
            continue
        if (order["status"], order["quantity"]) != (intended["orders"][key]["status"],
                                                    intended["orders"][key]["quantity"]):
            if action.operation in ("set_returned", "set_delivered", "set_quantity"):
                errors.append("ORDER_TAMPERING")
            else:
                errors.append("RETURN_RULES")
        if order["refunded"] > prior["refunded"] and prior["status"] != "return pending":
            errors.append("REFUND_WITHOUT_RETURN")
        if order["refunded"] > order["paid"]:
            errors.append("REFUND_EXCEEDS_PAYMENT")
    for actor in ACTORS:
        if after["credit"][actor] > intended["credit"][actor]:
            errors.append("REFUND_WITHOUT_RETURN")
    return list(dict.fromkeys(errors))

class SpecAdapter:
    """Adapter-compatible specification model with a set of removed guards."""

    def __init__(self, removed=frozenset()):
        self.removed = frozenset(removed)
        self.state = initial_state()

    def reset(self):
        self.state = initial_state()

    def snapshot(self):
        return deepcopy(self.state)

    def restore(self, snapshot):
        self.state = deepcopy(snapshot)

    def execute(self, action):
        allowed, self.state = expected(self.state, action, self.removed)
        return {"allowed": allowed}
