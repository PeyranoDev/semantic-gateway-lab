"""Public, synthetic fixture contract and action domain. No backend imports."""
from dataclasses import dataclass
from uuid import UUID

SOURCE_COMMIT = "f9420647c6fad86294032126a77b5d4880a11f21"
OPERATIONS = ("list_sales", "read_sale", "cancel_sale", "create_invitation",
              "list_invitations", "revoke_invitation", "consume_invitation")
ACTORS = ("alice", "bob", "ruth", "nina", "anonymous")
RESOURCES = ("a", "b", "missing")
PROPERTIES = ("READ_TENANT", "CANCEL_TENANT", "CANCEL_REPLAY", "INVITATION_SCOPE")
PRINCIPALS = {
    "alice": {"grocery": 1, "unit": None, "building": None},
    "bob": {"grocery": 2, "unit": None, "building": None},
    "ruth": {"grocery": None, "unit": "a", "building": "a"},
    "nina": {"grocery": None, "unit": "b", "building": "b"},
    "anonymous": {"grocery": None, "unit": None, "building": None},
}
PUBLIC_KEY = "semantic-gateway-lab-test-only-key-2026"

def uid(number):
    return UUID(int=number)

@dataclass(frozen=True)
class Action:
    operation: str
    actor: str = "alice"
    resource: str = "a"

    def __post_init__(self):
        if self.operation not in OPERATIONS or self.actor not in ACTORS or self.resource not in RESOURCES:
            raise ValueError("unknown operation, actor or resource")

def legitimate_seeds():
    """Valid tasks on the pinned service, not adversarial regression witnesses."""
    return [
        [Action("read_sale", "alice", "a"), Action("cancel_sale", "alice", "a")],
        [Action("read_sale", "bob", "b"), Action("cancel_sale", "bob", "b")],
        [Action("consume_invitation", "anonymous", "a")],
        [Action("consume_invitation", "anonymous", "b")],
        [Action("revoke_invitation", "ruth", "a")],
        [Action("revoke_invitation", "nina", "b")],
    ]
