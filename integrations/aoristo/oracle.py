"""Case-study specification, independent of routes, use cases and feedback.

This is an explicitly adopted research contract, not an inferred implementation.
Expired-token housekeeping is outside the v0.3 operation domain.
"""
from .model import PRINCIPALS

def check(before, action, response, after):
    errors = []
    code = response["status"]
    success = 200 <= code < 300
    actor = PRINCIPALS[action.actor]
    op, resource = action.operation, action.resource
    sale = before["sales"].get(resource)
    invitation = before["invitations"].get(resource)
    allowed = False
    cause = "AUTHORIZATION"
    expected = None
    if op in ("list_sales", "read_sale", "cancel_sale"):
        member = actor["grocery"] is not None
        if op == "list_sales":
            allowed = member
        elif sale:
            same = actor["grocery"] == sale["grocery"]
            cause = "READ_TENANT" if op == "read_sale" else "CANCEL_TENANT"
            allowed = member and same
            if op == "cancel_sale" and allowed:
                cause = "CANCEL_REPLAY" if sale["status"] == "cancelled" else "SALE_STATE"
                allowed = sale["status"] == "pending"
    elif op in ("create_invitation", "list_invitations", "revoke_invitation"):
        cause = "INVITATION_SCOPE"
        unit = invitation["unit"] if op == "revoke_invitation" and invitation else resource
        allowed = actor["unit"] is not None and actor["unit"] == unit and resource != "missing"
        if op == "revoke_invitation" and invitation is None:
            allowed = False
            cause = "NOT_FOUND"
    elif op == "consume_invitation":
        # Public endpoint accepts possession of a capability; no resident role needed.
        cause = "INVITATION_LIMIT"
        allowed = invitation is not None and invitation["uses"] < invitation["max_uses"]

    if not allowed:
        if success or before != after:
            errors.append(cause)
        if before != after:
            errors.append("DENIED_EFFECT")
    elif not success:
        errors.append("LEGITIMATE_TASK_BLOCKED")
        if before != after:
            errors.append("ERROR_EFFECT")
    if code >= 500:
        errors.append("SERVER_ERROR")

    if allowed and success:
        import copy
        expected = copy.deepcopy(before)
        if op == "cancel_sale":
            expected["sales"][resource]["status"] = "cancelled"
            expected["inventory"][str(sale["grocery"])] += sale["quantity"]
        elif op == "consume_invitation":
            expected["invitations"][resource]["uses"] += 1
        elif op == "revoke_invitation":
            del expected["invitations"][resource]
        elif op == "create_invitation":
            # A successful create must add exactly one invitation in the requested unit.
            old = expected["invitations"]
            new = {k: v for k, v in after["invitations"].items() if k not in old}
            valid = (len(new) == 1 and all(v == {"unit": resource, "uses": 0, "max_uses": 1}
                                         for v in new.values()))
            if valid:
                old.update(new)
        if expected != after:
            errors.append("UNEXPECTED_EFFECT")
        if op == "read_sale":
            if response["body"].get("data", {}).get("id") != {"a": 1, "b": 2}.get(resource):
                errors.append("OUTPUT_MISMATCH")
        if op == "list_sales":
            # Public response omits GroceryId: bind output IDs to the observed fixture.
            data = response["body"].get("data", [])
            ids = {v["id"] for v in data} if isinstance(data, list) else None
            expected_ids = { {"a": 1, "b": 2}[key] for key, value in before["sales"].items()
                             if value["grocery"] == actor["grocery"] }
            if ids != expected_ids:
                errors.append("OUTPUT_SCOPE")
    return list(dict.fromkeys(errors))
