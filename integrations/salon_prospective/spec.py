"""Specification-level counterparts of the implementation mutants.

The same guard disjunct is removed from the specification's `expected()` model
(read from integrations/salon/oracle.py, never edited). Predictions computed on
these models use no implementation behavior. The unmutated oracle still judges.
"""
import ast
from copy import deepcopy
from pathlib import Path

import integrations.salon.oracle as oracle_module
from integrations.salon.model import Action

SOURCE = Path(oracle_module.__file__)
TRANSITIONS = ("reserve", "pay", "confirm", "cancel", "refund")
# implementation site -> (specification line:disjunct, operations the implementation guard covers)
MAPPING = {
    "read:31:0": ("28:0", ("read_booking",)), "read:31:1": ("30:0", ("read_booking",)),
    "transition:51:0": ("28:0", TRANSITIONS), "transition:51:1": ("30:0", TRANSITIONS),
    "transition:54:0": ("36:0", None), "transition:57:0": ("39:0", None),
    "transition:59:0": ("41:0", None), "transition:64:0": ("46:0", None),
    "transition:64:1": ("46:1", None), "transition:66:0": ("48:0", None),
    "transition:66:1": ("48:1", None), "transition:69:0": ("48:2", None),
    "transition:76:0": ("55:0", None), "transition:76:1": ("57:0", None),
    "transition:81:0": ("61:0", None), "transition:86:0": ("66:0", None),
    "transition:86:1": ("66:1", None), "transition:86:2": ("68:0", None),
}

def _parts(test):
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.Or):
        return test.values
    return [test]

def mutant_expected(site_id):
    """Compile `expected` with the mapped guard disjunct disabled for the mapped operations."""
    spec_site, operations = MAPPING[site_id]
    line, index = map(int, spec_site.split(":"))
    tree = ast.parse(SOURCE.read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "expected")
    node = next(n for n in ast.walk(function) if isinstance(n, ast.If) and n.lineno == line)
    parts = _parts(node.test)
    replacement = (ast.Constant(False) if operations is None else
                   ast.BoolOp(ast.And(), [parts[index], ast.Compare(
                       ast.Name("op", ast.Load()), [ast.NotIn()],
                       [ast.Tuple([ast.Constant(o) for o in operations], ast.Load())])]))
    if len(parts) == 1:
        node.test = replacement
    else:
        parts[index] = replacement
    ast.fix_missing_locations(tree)
    namespace = {"__name__": "integrations.salon.oracle_mutant"}
    exec(compile(tree, f"<spec mutant {site_id}>", "exec"), namespace)
    return namespace["expected"]

class SpecAdapter:
    """Adapter-compatible model of a specification mutant; exceptions model a 500 response."""

    def __init__(self, expected, initial):
        self.expected, self.initial = expected, initial
        self.state = deepcopy(initial)

    def reset(self):
        self.state = deepcopy(self.initial)

    def snapshot(self):
        return deepcopy(self.state)

    def restore(self, snapshot):
        self.state = deepcopy(snapshot)

    def execute(self, action: Action):
        try:
            status, after, body, cause = self.expected(self.state, action)
        except Exception:  # noqa: BLE001 - a crashing guard-free path is a server error
            return {"status": 500, "body": {"detail": "server error"}}
        self.state = after
        return {"status": status, "body": body if status == 200 else {"detail": cause}}
