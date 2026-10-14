"""Observational projections; these neither filter actions nor authorize requests."""
import json

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))

def project(state, mode):
    enabled = ["list_bookings", "read_booking"]
    for booking in state["bookings"].values():
        slot = state["slots"][booking["slot"]]
        if booking["status"] == "draft" and slot["occupied"] < slot["capacity"]:
            enabled.append("reserve")
        if booking["status"] == "reserved":
            if not booking["paid"]:
                enabled.append("pay")
            if booking["paid"] == slot["price"]:
                enabled.append("confirm")
        if booking["status"] in ("reserved", "confirmed"):
            enabled.append("cancel")
        if booking["status"] == "cancelled" and booking["paid"] and not booking["refunded"]:
            enabled.append("refund")
    enabled = sorted(set(enabled))
    if mode == "sequence_enabled":
        return canonical(enabled)
    if mode == "sequence_enriched":
        return canonical([enabled, state])
    raise ValueError("unknown feedback mode")
