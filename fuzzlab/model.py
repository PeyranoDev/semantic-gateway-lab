"""Shared data types and finite fixture; no authorization decisions."""
from dataclasses import asdict, dataclass, field
import hashlib
import hmac
import json

TOOLS = ("list_documents", "read_document", "create_document", "update_document",
         "initiate_share", "accept_share", "revoke_share", "request_delete",
         "delete_document", "export_document")
MUTANTS = ("cross_department_read", "wrong_recipient", "sharing_overwrite",
           "unauthorized_revoke", "approval_scope", "approval_replay",
           "missing_approval", "deny_audit")
STRATEGIES = ("random", "enabled", "enriched")
# Public TEST KEY, not a credential. The trusted fixture alone signs approvals.
TEST_KEY = b"semantic-gateway-lab-public-fixture-key"
NOW = 1000

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))

@dataclass(frozen=True)
class Principal:
    department: str
    role: str

@dataclass
class Document:
    owner: str
    department: str
    content: str = "confidential"
    phase: str = "draft"
    pending: str | None = None
    acl: list[str] = field(default_factory=list)
    delete_requested: bool = False

@dataclass(frozen=True)
class Action:
    tool: str
    actor: str = "alice"
    document: str = "d1"
    target: str = "bob"
    content: str = "updated"
    token: str = ""

@dataclass
class State:
    principals: dict[str, Principal]
    documents: dict[str, Document]
    used_nonces: list[str] = field(default_factory=list)
    audit: list[dict] = field(default_factory=list)

    def snapshot(self):
        return asdict(self)

def initial_state():
    return State(
        {"alice": Principal("Finance", "Manager"),
         "bob": Principal("Finance", "Analyst"),
         "carol": Principal("Legal", "Manager"),
         "mallory": Principal("Finance", "Analyst")},
        {"d1": Document("alice", "Finance", "finance-secret"),
         "d2": Document("carol", "Legal", "legal-secret"),
         "d3": Document("alice", "Finance", "other-finance-secret")})

def fixture_approval(document="d1", actor="alice", nonce="n1", expires=2000):
    payload = {"actor": actor, "document": document, "operation": "delete_document",
               "nonce": nonce, "expires": expires}
    body = canonical(payload)
    return canonical({"payload": payload,
                      "mac": hmac.new(TEST_KEY, body.encode(), hashlib.sha256).hexdigest()})

def token_pool():
    return ("", "forged", fixture_approval(),
            fixture_approval("d2", "carol", "n2"),
            fixture_approval("d3", "alice", "n3"),
            fixture_approval(expires=999, nonce="expired"))
