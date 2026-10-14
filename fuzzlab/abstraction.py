"""Two observational feedback abstractions, not proven sound EPAs.

Enabledness here is existential lifecycle enabledness across fixture objects.
It is a deliberately coarse baseline, not parameter-specific authorization.
Both strategies see the same concrete snapshots; neither sees mutant labels.
"""
from .model import canonical

DOCUMENT_IDS = ("d1", "d2", "d3", "d4", "missing")

def enabled_tools(state):
    tools = {"list_documents"}
    docs = state["documents"]
    if any(k not in docs for k in DOCUMENT_IDS):
        tools.add("create_document")
    if docs:
        tools.update(("read_document", "export_document", "update_document"))
    for d in docs.values():
        if d["phase"] == "draft":
            tools.update(("initiate_share", "request_delete"))
            if d["delete_requested"]:
                tools.add("delete_document")
        if d["phase"] == "pending":
            tools.add("accept_share")
        if d["phase"] in ("pending", "shared"):
            tools.add("revoke_share")
    return tuple(sorted(tools))

def abstract(state, strategy):
    tools = enabled_tools(state)
    if strategy == "enabled":
        return canonical(tools)
    if strategy != "enriched":
        raise ValueError("unknown feedback abstraction")
    predicates = []
    for identifier in DOCUMENT_IDS:
        d = state["documents"].get(identifier)
        if d is None:
            predicates.append(None)
            continue
        relations = [(p["department"] == d["department"], actor == d["owner"],
                      actor == d["pending"], actor in d["acl"])
                     for actor, p in sorted(state["principals"].items())]
        predicates.append((d["phase"], d["delete_requested"], relations))
    return canonical((tools, predicates, sorted(state["used_nonces"])))

def concrete_key(state):
    # Common instrumentation across strategies; audit does not define business state.
    return canonical({"documents": state["documents"], "used_nonces": state["used_nonces"]})
