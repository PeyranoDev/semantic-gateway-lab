"""Explicit regression witnesses, never used as fuzzer seeds or rewards."""
from .model import Action, fixture_approval

def regression_witnesses():
    share = Action("initiate_share", target="bob")
    request = Action("request_delete")
    delete = Action("delete_document", token=fixture_approval())
    return {
        "cross_department_read": ("READ_SCOPE", [Action("read_document", actor="bob", document="d2")]),
        "wrong_recipient": ("SHARE_RECIPIENT", [share, Action("accept_share", actor="mallory")]),
        "sharing_overwrite": ("SHARE_PHASE", [share, Action("accept_share", actor="bob"),
                                               Action("accept_share", actor="mallory")]),
        "unauthorized_revoke": ("REVOKE_OWNER", [share, Action("revoke_share", actor="carol")]),
        "approval_scope": ("APPROVAL_SCOPE", [Action("request_delete", document="d3"),
                              Action("delete_document", document="d3", token=fixture_approval())]),
        "approval_replay": ("APPROVAL_REPLAY", [request, delete, Action("create_document"), request, delete]),
        "missing_approval": ("DELETE_APPROVAL", [request, Action("delete_document")]),
        "deny_audit": ("AUDIT_COMPLETENESS", [Action("read_document", actor="bob", document="d2")]),
    }

def legitimate_workflow():
    return [Action("list_documents"), Action("read_document"),
            Action("initiate_share", target="bob"), Action("accept_share", actor="bob"),
            Action("export_document", actor="bob"), Action("revoke_share"),
            Action("update_document", content="new report"), Action("request_delete"),
            Action("delete_document", token=fixture_approval()),
            Action("create_document", content="replacement"), Action("read_document")]
