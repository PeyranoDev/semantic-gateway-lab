"""Legitimate task controls and explicit injected-defect checks, outside campaign costs."""
from .experiment import replay
from .model import Action, VARIANT_TARGET, legitimate_seeds

def witnesses():
    return {
        "read_scope": [Action("read_booking", "alice", "b")],
        "slot_capacity": [Action("reserve"), Action("reserve", "alice", "a2")],
        "confirm_unpaid": [Action("reserve"), Action("confirm", "staff_a")],
        "refund_replay": [Action("reserve"), Action("pay"), Action("cancel"),
                          Action("refund", "staff_a"), Action("refund", "staff_a")],
    }

def validate(adapter, variant):
    result = []
    for index, seed in enumerate(legitimate_seeds()):
        trace = replay(adapter, seed)
        assert all(not s["violations"] and s["response"]["status"] == 200 for s in trace), trace
        result.append({"case": "legitimate_workflow_" + str(index), "passed": True, "trace": trace})
    for mutant, program in witnesses().items():
        trace = replay(adapter, program)
        errors = [e for s in trace for e in s["violations"]]
        wanted = VARIANT_TARGET[mutant] if variant == mutant else None
        assert (wanted in errors if wanted else not errors), (variant, mutant, errors)
        result.append({"case": mutant, "passed": True,
                       "expected_violation": wanted, "trace": trace})
    return result
