"""Observational projections. These never authorize an operation."""
import json

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))

def project(state, mode):
    enabled = ["list_sales", "read_sale", "create_invitation", "list_invitations"]
    if any(s["status"] == "pending" for s in state["sales"].values()):
        enabled.append("cancel_sale")
    if state["invitations"]:
        enabled.append("revoke_invitation")
    if any(i["uses"] < i["max_uses"] for i in state["invitations"].values()):
        enabled.append("consume_invitation")
    if mode == "sequence_enabled":
        return canonical(sorted(enabled))
    if mode == "sequence_enriched":
        # Named resource scope, lifecycle, capability counts and inventory effects.
        return canonical([sorted(enabled), state])
    raise ValueError("unknown feedback mode")
