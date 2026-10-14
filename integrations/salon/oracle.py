"""Adopted business specification, with independent decisions, SQL effects and outputs."""
from copy import deepcopy
from .model import PRINCIPALS

def _view(identifier, row):
    return {"id": identifier, **row}

def _scope(actor, row, name):
    if actor["tenant"] != row["tenant"]:
        return False
    if actor["role"] == "staff":
        return True
    return actor["role"] == "customer" and row["customer"] == name

def expected(before, action):
    """Pure expected response code, state, public output and denial reason."""
    after = deepcopy(before)
    actor = PRINCIPALS[action.actor]
    op, key = action.operation, action.resource
    row = before["bookings"].get(key)
    cause = "BUSINESS_STATE"
    if actor["role"] is None:
        return 401, after, None, "AUTHENTICATION"
    if op == "list_bookings":
        data = [_view(k, v) for k, v in sorted(before["bookings"].items())
                if _scope(actor, v, action.actor)]
        return 200, after, data, cause
    if row is None:
        return 404, after, None, "NOT_FOUND"
    if not _scope(actor, row, action.actor):
        return 404, after, None, "BOOKING_SCOPE"
    slot = before["slots"][row["slot"]]
    booking = after["bookings"][key]
    if op == "read_booking":
        return 200, after, _view(key, row), cause
    if op in ("confirm", "refund") and actor["role"] != "staff":
        return 403, after, None, "STAFF_ROLE"
    if op == "reserve":
        if row["status"] != "draft":
            return 409, after, None, cause
        if slot["occupied"] >= slot["capacity"]:
            return 409, after, None, "SLOT_CAPACITY"
        booking["status"] = "reserved"
        after["slots"][row["slot"]]["occupied"] += 1
    elif op == "pay":
        if actor["role"] != "customer" or row["customer"] != action.actor:
            return 403, after, None, "CUSTOMER_ROLE"
        if row["status"] != "reserved" or row["paid"] or before["users"][action.actor]["balance"] < slot["price"]:
            return 409, after, None, cause
        booking["paid"] = slot["price"]
        after["users"][action.actor]["balance"] -= slot["price"]
        after["ledger"].append({"booking": key, "customer": action.actor,
                               "kind": "payment", "amount": slot["price"]})
    elif op == "confirm":
        if row["status"] != "reserved":
            return 409, after, None, cause
        if row["paid"] != slot["price"]:
            return 409, after, None, "CONFIRM_PAYMENT"
        booking["status"] = "confirmed"
    elif op == "cancel":
        if row["status"] not in ("reserved", "confirmed"):
            return 409, after, None, cause
        booking["status"] = "cancelled"
        after["slots"][row["slot"]]["occupied"] -= 1
    elif op == "refund":
        if row["status"] != "cancelled" or not row["paid"]:
            return 409, after, None, cause
        if row["refunded"]:
            return 409, after, None, "REFUND_REPLAY"
        booking["refunded"] = row["paid"]
        after["users"][row["customer"]]["balance"] += row["paid"]
        after["ledger"].append({"booking": key, "customer": row["customer"],
                               "kind": "refund", "amount": row["paid"]})
    return 200, after, _view(key, booking), cause

def check(before, action, response, after):
    status, wanted, body, cause = expected(before, action)
    errors = []
    if response["status"] != status:
        errors.append(cause if status >= 400 else "LEGITIMATE_TASK_BLOCKED")
    if after != wanted:
        errors.append(cause if status >= 400 else "UNEXPECTED_EFFECT")
        if status >= 400:
            errors.append("DENIED_EFFECT")
    if status == 200 and response["status"] == 200 and response["body"] != body:
        errors.append("OUTPUT_MISMATCH")
    if response["status"] >= 500:
        errors.append("SERVER_ERROR")
    # Additional history invariants independent of the transition guard.
    for key, slot in after["slots"].items():
        occupied = sum(b["slot"] == key and b["status"] in ("reserved", "confirmed")
                       for b in after["bookings"].values())
        if slot["occupied"] != occupied or not 0 <= occupied <= slot["capacity"]:
            errors.append("SLOT_CAPACITY")
    for key, booking in after["bookings"].items():
        if booking["status"] == "confirmed" and booking["paid"] != after["slots"][booking["slot"]]["price"]:
            errors.append("CONFIRM_PAYMENT")
        refunds = [r["amount"] for r in after["ledger"] if r["booking"] == key and r["kind"] == "refund"]
        if len(refunds) > 1 or sum(refunds) > booking["paid"]:
            errors.append("REFUND_REPLAY")
    for user, info in after["users"].items():
        if info["role"] != "customer":
            continue
        net = sum((1 if entry["kind"] == "refund" else -1) * entry["amount"]
                  for entry in after["ledger"] if entry["customer"] == user)
        if info["balance"] != 5000 + net:
            errors.append("LEDGER_BALANCE")
    return list(dict.fromkeys(errors))
