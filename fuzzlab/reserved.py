"""Reserved synthetic implementation variants, not independently sourced defects."""
from .backend import Gateway

RESERVED = ("list_scope", "unauthorized_update", "cross_department_share")

class ReservedGateway(Gateway):
    def __init__(self, variant):
        if variant not in RESERVED:
            raise ValueError("unknown reserved variant")
        super().__init__("fixed")
        self.variant = variant

    def _execute(self, action):
        p = self.state.principals.get(action.actor)
        d = self.state.documents.get(action.document)
        if self.variant == "list_scope" and action.tool == "list_documents" and p:
            return {"allowed": True, "data": sorted(self.state.documents)}
        if self.variant == "unauthorized_update" and action.tool == "update_document" and p and d:
            if p.department == d.department:
                d.content = action.content
                return {"allowed": True, "data": None}
        if self.variant == "cross_department_share" and action.tool == "initiate_share" and p and d:
            target = self.state.principals.get(action.target)
            if (p.role == "Manager" and d.owner == action.actor and p.department == d.department
                    and d.phase == "draft" and target and action.target != action.actor):
                d.phase, d.pending = "pending", action.target
                return {"allowed": True, "data": None}
        return super()._execute(action)

def gateway(variant):
    return ReservedGateway(variant) if variant in RESERVED else Gateway(variant)
