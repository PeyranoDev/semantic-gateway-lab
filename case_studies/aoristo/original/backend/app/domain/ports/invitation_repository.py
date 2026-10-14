"""
Domain port for Invitation repository.
"""
from typing import Protocol, Optional, List
from uuid import UUID

from ..entities.redvecina import Invitation


class InvitationRepositoryPort(Protocol):
    def create(self, invitation: Invitation) -> Invitation:
        ...

    def get_by_id(self, invitation_id: UUID) -> Optional[Invitation]:
        ...

    def get_by_token(self, token: str) -> Optional[Invitation]:
        ...

    def get_by_unit(self, unit_id: UUID) -> List[Invitation]:
        ...

    def increment_uses(self, invitation_id: UUID) -> Optional[Invitation]:
        ...

    def update(self, invitation: Invitation) -> Invitation:
        ...

    def delete(self, invitation_id: UUID) -> bool:
        ...
