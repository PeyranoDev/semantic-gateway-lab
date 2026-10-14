"""Finite research contract. No backend imports."""
from dataclasses import dataclass

OPERATIONS = ("list_bookings", "read_booking", "reserve", "pay", "confirm", "cancel", "refund")
ACTORS = ("alice", "bob", "staff_a", "staff_b", "anonymous")
RESOURCES = ("a", "a2", "b", "b2", "missing")
PROPERTIES = ("BOOKING_SCOPE", "SLOT_CAPACITY", "CONFIRM_PAYMENT", "REFUND_REPLAY")
VARIANT_TARGET = {"read_scope": "BOOKING_SCOPE", "slot_capacity": "SLOT_CAPACITY",
                  "confirm_unpaid": "CONFIRM_PAYMENT", "refund_replay": "REFUND_REPLAY"}
PRINCIPALS = {
    "alice": {"tenant": "a", "role": "customer"},
    "bob": {"tenant": "b", "role": "customer"},
    "staff_a": {"tenant": "a", "role": "staff"},
    "staff_b": {"tenant": "b", "role": "staff"},
    "anonymous": {"tenant": None, "role": None},
}
PUBLIC_KEY = "salon-research-public-fixture-signing-key-only"

@dataclass(frozen=True)
class Action:
    operation: str
    actor: str = "alice"
    resource: str = "a"

    def __post_init__(self):
        if self.operation not in OPERATIONS or self.actor not in ACTORS or self.resource not in RESOURCES:
            raise ValueError("unknown operation, actor or resource")

def legitimate_seeds():
    """Valid business tasks, never a failing/repeated refund or overbooking seed."""
    programs = []
    for tenant, customer, staff in (("a", "alice", "staff_a"), ("b", "bob", "staff_b")):
        programs.extend([
            [Action("reserve", customer, tenant), Action("pay", customer, tenant),
             Action("confirm", staff, tenant)],
            [Action("reserve", customer, tenant), Action("pay", customer, tenant),
             Action("cancel", customer, tenant), Action("refund", staff, tenant)],
            [Action("reserve", customer, tenant), Action("cancel", customer, tenant),
             Action("reserve", customer, tenant + "2")],
            [Action("list_bookings", customer, tenant), Action("read_booking", customer, tenant)],
        ])
    return programs
