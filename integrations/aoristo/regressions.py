"""Reviewed, known witnesses. Never imported by the generator or campaign."""
from .experiment import replay
from .model import Action, legitimate_seeds

CASES = {
    "cancel_replay": ([Action("cancel_sale"), Action("cancel_sale")], "CANCEL_REPLAY"),
    "read_foreign_sale": ([Action("read_sale", "alice", "b")], "READ_TENANT"),
    "cancel_foreign_sale": ([Action("cancel_sale", "alice", "b")], "CANCEL_TENANT"),
    "revoke_foreign_invitation": ([Action("revoke_invitation", "ruth", "b")], "INVITATION_SCOPE"),
    "create_foreign_invitation": ([Action("create_invitation", "ruth", "b")], "INVITATION_SCOPE"),
    "create_own_invitation_response": ([Action("create_invitation", "ruth", "a")], "ERROR_EFFECT"),
    "list_own_invitation_response": ([Action("list_invitations", "ruth", "a")], "SERVER_ERROR"),
}

def validate(adapter):
    controls = []
    for index, program in enumerate(legitimate_seeds()):
        trace = replay(adapter, program)
        if any(step["violations"] for step in trace):
            raise AssertionError(f"legitimate seed {index} failed: {trace}")
        controls.append({"name": f"seed-{index}", "trace": trace})
    for name, program in {
        "list_own_sales": [Action("list_sales")],
        "reject_anonymous": [Action("read_sale", "anonymous")],
        "reject_cross_product": [Action("read_sale", "ruth"), Action("revoke_invitation", "alice")],
        "invitation_usage_limit": [Action("consume_invitation", "anonymous")]*2,
        "revoked_invitation": [Action("revoke_invitation", "ruth"), Action("consume_invitation", "anonymous")],
    }.items():
        trace = replay(adapter, program)
        if any(step["violations"] for step in trace):
            raise AssertionError(f"control {name} failed: {trace}")
        controls.append({"name": name, "trace": trace})
    witnesses = []
    for name, (program, target) in CASES.items():
        trace = replay(adapter, program)
        if not any(target in step["violations"] for step in trace):
            raise AssertionError(f"known pinned-source witness {name} not reproduced: {trace}")
        witnesses.append({"name": name, "target": target, "trace": trace})
    return {"controls": controls, "known_witnesses": witnesses,
            "controls_passed": len(controls), "known_witnesses_reproduced": len(witnesses)}
