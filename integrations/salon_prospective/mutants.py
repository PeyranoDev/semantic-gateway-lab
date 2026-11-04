"""Systematic guard-disjunct removal mutants of the salon service.

Every `if <A or B or ...>: raise ...` guard in the request paths reachable from the
campaign domain yields one mutant per top-level disjunct, with that disjunct
replaced by False. No mutant is selected by hand. The measured service source is
read, never edited; mutants are compiled in memory and injected only while a
research adapter is constructed.
"""
import ast
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import backends.salon.service as service_module

SOURCE = Path(service_module.__file__)
METHODS = ("read", "transition")  # create() is outside the finite campaign domain
# Existing deliberate variants coincide with these sites under variant="fixed".
EXISTING = {"read:31:1": "read_scope", "transition:59:0": "slot_capacity",
            "transition:76:1": "confirm_unpaid", "transition:86:2": "refund_replay"}

def _disjuncts(test):
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.Or):
        return test.values
    return [test]

def _guards(tree):
    service = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "SalonService")
    for method in service.body:
        if not isinstance(method, ast.FunctionDef) or method.name not in METHODS:
            continue
        for node in ast.walk(method):
            if isinstance(node, ast.If) and any(isinstance(s, ast.Raise) for s in node.body):
                yield method.name, node

def sites():
    """Ordered mutant identifiers `method:line:disjunct` with their removed condition."""
    tree = ast.parse(SOURCE.read_text())
    out = []
    for method, node in _guards(tree):
        for index, disjunct in enumerate(_disjuncts(node.test)):
            out.append({"id": f"{method}:{node.lineno}:{index}", "removed": ast.unparse(disjunct),
                        "existing_variant": EXISTING.get(f"{method}:{node.lineno}:{index}")})
    return out

def mutant_class(site_id):
    method_name, line, index = site_id.split(":")
    tree = ast.parse(SOURCE.read_text())
    for method, node in _guards(tree):
        if method == method_name and node.lineno == int(line):
            parts = _disjuncts(node.test)
            if len(parts) == 1:
                node.test = ast.Constant(False)
            else:
                parts[int(index)] = ast.Constant(False)
            break
    else:
        raise ValueError("unknown mutant site")
    ast.fix_missing_locations(tree)
    namespace = {"__name__": "backends.salon.service_mutant"}
    exec(compile(tree, f"<mutant {site_id}>", "exec"), namespace)
    return namespace["SalonService"]

@contextmanager
def injected(site_id):
    """Construct research adapters whose service is the given mutant (variant='fixed')."""
    with patch("backends.salon.app.SalonService", mutant_class(site_id)):
        yield
