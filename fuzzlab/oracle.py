"""Independent specification oracle over snapshots and observable responses.

Does not import Gateway, its policy helpers, mutants, or the abstractions.
The specification deliberately duplicates the small reference semantics so
a missing implementation check is not also silently missing from the oracle.
"""
import copy
import hashlib
import hmac
import json
from dataclasses import asdict
from .model import TEST_KEY, NOW

def inspect(before, action, result, after):
    a = asdict(action)
    p = before["principals"].get(a["actor"])
    doc = before["documents"].get(a["document"])
    expected = copy.deepcopy(before)
    authorized = False
    data = None
    failure = "AUTHORIZATION"
    owned = bool(p and doc and p["role"] == "Manager" and doc["owner"] == a["actor"]
                 and p["department"] == doc["department"])
    can_read = lambda d: bool(p and p["department"] == d["department"]
                             and (a["actor"] == d["owner"] or a["actor"] in d["acl"]))
    if a["tool"] == "list_documents" and p:
        authorized = True
        data = sorted(k for k, d in before["documents"].items() if can_read(d))
    elif a["tool"] == "create_document":
        authorized = bool(p and p["role"] == "Manager" and doc is None)
        if authorized:
            expected["documents"][a["document"]] = dict(owner=a["actor"], department=p["department"],
                content=a["content"], phase="draft", pending=None, acl=[], delete_requested=False)
    elif doc:
        d = expected["documents"][a["document"]]
        tool = a["tool"]
        if tool in ("read_document", "export_document"):
            authorized, failure = can_read(doc), "READ_SCOPE"
            data = doc["content"] if authorized else None
        elif tool == "update_document":
            authorized = owned
            if authorized:
                d["content"] = a["content"]
        elif tool == "initiate_share":
            target = before["principals"].get(a["target"])
            authorized = bool(owned and doc["phase"] == "draft" and target
                              and target["department"] == doc["department"] and a["target"] != a["actor"])
            if authorized:
                d["phase"], d["pending"] = "pending", a["target"]
        elif tool == "accept_share":
            failure = "SHARE_PHASE" if doc["phase"] != "pending" else "SHARE_RECIPIENT"
            authorized = bool(p and doc["phase"] == "pending" and doc["pending"] == a["actor"]
                              and p["department"] == doc["department"])
            if authorized:
                d["phase"], d["pending"], d["acl"] = "shared", None, [a["actor"]]
        elif tool == "revoke_share":
            authorized, failure = owned and doc["phase"] in ("pending", "shared"), "REVOKE_OWNER"
            if authorized:
                d["phase"], d["pending"], d["acl"] = "draft", None, []
        elif tool == "request_delete":
            authorized = owned and doc["phase"] == "draft"
            if authorized:
                d["delete_requested"] = True
        elif tool == "delete_document":
            # Separate verification implementation; no call to Gateway._approval.
            failure = "DELETE_APPROVAL"
            nonce = None
            try:
                envelope = json.loads(a["token"])
                claim = envelope["payload"]
                body = json.dumps(claim, sort_keys=True, separators=(",", ":")).encode()
                mac = hmac.new(TEST_KEY, body, hashlib.sha256).hexdigest()
                valid = hmac.compare_digest(mac, envelope["mac"])
                valid = valid and isinstance(claim["expires"], int) and claim["expires"] > NOW
                if claim["actor"] != a["actor"] or claim["document"] != a["document"] or claim["operation"] != tool:
                    failure, valid = "APPROVAL_SCOPE", False
                if claim["nonce"] in before["used_nonces"]:
                    failure, valid = "APPROVAL_REPLAY", False
                if valid:
                    nonce = claim["nonce"]
            except (KeyError, TypeError, ValueError):
                pass
            authorized = owned and doc["phase"] == "draft" and doc["delete_requested"] and nonce is not None
            if authorized:
                expected["used_nonces"].append(nonce)
                del expected["documents"][a["document"]]
    violations = []
    if result["allowed"] and not authorized:
        violations.append(failure)
    elif authorized and not result["allowed"]:
        violations.append("LEGITIMATE_TASK_BLOCKED")
    if not result["allowed"]:
        expected = copy.deepcopy(before)
    if after["documents"] != expected["documents"] or after["used_nonces"] != expected["used_nonces"]:
        violations.append("UNEXPECTED_EFFECT" if result["allowed"] else "DENY_MUTATED_STATE")
    if result["data"] != (data if result["allowed"] else None):
        violations.append("OUTPUT_MISMATCH")
    expected_audit = before["audit"] + [{"action": a, "allowed": result["allowed"]}]
    if after["audit"] != expected_audit:
        violations.append("AUDIT_COMPLETENESS")
    if after["principals"] != before["principals"]:
        violations.append("IDENTITY_MUTATION")
    return violations
