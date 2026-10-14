"""Executable in-memory document service with isolated implementation mutants.

Mutant flags change actual checks/effects. They are not visible to the fuzzer
or to the oracle. Authenticated principals come from the harness, not tool args.
"""
import hashlib
import hmac
import json
from dataclasses import asdict
from .model import TEST_KEY, NOW, MUTANTS, TOOLS, Document, canonical, initial_state

class Gateway:
    def __init__(self, mutant="fixed"):
        if mutant not in ("fixed", *MUTANTS):
            raise ValueError("unknown mutant")
        self.mutant = mutant
        self.state = initial_state()

    def _approval(self, action):
        try:
            envelope = json.loads(action.token)
            payload = envelope["payload"]
            signature = hmac.new(TEST_KEY, canonical(payload).encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, envelope["mac"]):
                return None
            if not isinstance(payload["expires"], int) or payload["expires"] <= NOW:
                return None
            if self.mutant != "approval_scope" and (
                payload["actor"] != action.actor or payload["document"] != action.document
                or payload["operation"] != "delete_document"
            ):
                return None
            if self.mutant != "approval_replay" and payload["nonce"] in self.state.used_nonces:
                return None
            return payload["nonce"]
        except (KeyError, TypeError, ValueError):
            return None

    def execute(self, action):
        result = self._execute(action)
        if result["allowed"] or self.mutant != "deny_audit":
            self.state.audit.append({"action": asdict(action), "allowed": result["allowed"]})
        return result

    def _execute(self, a):
        deny = {"allowed": False, "data": None}
        s = self.state
        p = s.principals.get(a.actor)
        if p is None or a.tool not in TOOLS:
            return deny
        def readable(d):
            return d.department == p.department and (d.owner == a.actor or a.actor in d.acl)
        def manageable(d):
            return p.role == "Manager" and d.department == p.department and d.owner == a.actor
        if a.tool == "list_documents":
            return {"allowed": True, "data": sorted(k for k, d in s.documents.items() if readable(d))}
        if a.tool == "create_document":
            if p.role != "Manager" or a.document in s.documents:
                return deny
            s.documents[a.document] = Document(a.actor, p.department, a.content)
            return {"allowed": True, "data": None}
        d = s.documents.get(a.document)
        if d is None:
            return deny
        if a.tool in ("read_document", "export_document"):
            if not readable(d) and self.mutant != "cross_department_read":
                return deny
            return {"allowed": True, "data": d.content}
        if a.tool == "accept_share":
            good_phase = d.phase == "pending" or (self.mutant == "sharing_overwrite" and d.phase == "shared")
            good_recipient = d.pending == a.actor or self.mutant == "wrong_recipient"
            if self.mutant == "sharing_overwrite" and d.phase == "shared":
                good_recipient = True
            if not good_phase or not good_recipient or p.department != d.department:
                return deny
            d.acl = [a.actor]
            d.pending = None
            d.phase = "shared"
            return {"allowed": True, "data": None}
        if not manageable(d) and not (a.tool == "revoke_share" and self.mutant == "unauthorized_revoke"):
            return deny
        if a.tool == "update_document":
            d.content = a.content
        elif a.tool == "initiate_share":
            target = s.principals.get(a.target)
            if d.phase != "draft" or target is None or target.department != d.department or a.target == a.actor:
                return deny
            d.phase, d.pending = "pending", a.target
        elif a.tool == "revoke_share":
            if d.phase not in ("pending", "shared"):
                return deny
            d.phase, d.pending, d.acl = "draft", None, []
        elif a.tool == "request_delete":
            if d.phase != "draft":
                return deny
            d.delete_requested = True
        elif a.tool == "delete_document":
            if d.phase != "draft" or not d.delete_requested:
                return deny
            nonce = self._approval(a)
            if nonce is None and self.mutant != "missing_approval":
                return deny
            if nonce is not None:
                s.used_nonces.append(nonce)
            del s.documents[a.document]
        else:
            return deny
        return {"allowed": True, "data": None}
