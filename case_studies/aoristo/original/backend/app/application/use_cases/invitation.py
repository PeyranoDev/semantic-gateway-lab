"""
Invitation Link Use Cases.
"""
from typing import List
from uuid import UUID
from datetime import datetime, timedelta
import secrets

from app.domain.entities.redvecina import Invitation
from app.domain.ports.invitation_repository import InvitationRepositoryPort
from app.domain.ports.building_repository import UnitRepositoryPort


class InvitationNotFoundError(Exception):
    """Raised when invitation is not found."""
    pass


class InvitationExpiredError(Exception):
    """Raised when invitation has expired."""
    pass


class InvitationExhaustedError(Exception):
    """Raised when invitation has reached max uses."""
    pass


class GenerateInvitationUseCase:
    """Generate invitation link for new residents."""
    
    def __init__(
        self,
        invitation_repo: InvitationRepositoryPort,
        unit_repo: UnitRepositoryPort,
    ):
        self.invitation_repo = invitation_repo
        self.unit_repo = unit_repo
    
    def _generate_token(self) -> str:
        """Generate secure random token."""
        return secrets.token_urlsafe(32)
    
    def execute(
        self,
        unit_id: UUID,
        max_uses: int = 5,
        valid_days: int = 7,
    ) -> Invitation:
        """Generate invitation."""
        # Validate unit exists
        unit = self.unit_repo.get_by_id(unit_id)
        if not unit:
            raise ValueError(f"Unit {unit_id} not found")
        
        # Generate token
        token = self._generate_token()
        
        # Set expiration
        expires_at = datetime.utcnow() + timedelta(days=valid_days)
        
        invitation = Invitation(
            id=None,
            unit_id=unit_id,
            token=token,
            current_uses=0,
            max_uses=max_uses,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
        )
        return self.invitation_repo.create(invitation)


class ValidateInvitationUseCase:
    """Validate and consume an invitation."""
    
    def __init__(self, invitation_repo: InvitationRepositoryPort):
        self.invitation_repo = invitation_repo
    
    def execute(self, token: str) -> Invitation:
        """Validate invitation and increment uses."""
        # Find invitation
        invitation = self.invitation_repo.get_by_token(token)
        if not invitation:
            raise InvitationNotFoundError("Invitation not found")
        
        # Check expiration
        if datetime.utcnow() > invitation.expires_at:
            raise InvitationExpiredError("Invitation has expired")
        
        # Check uses
        if invitation.current_uses >= invitation.max_uses:
            raise InvitationExhaustedError("Invitation has reached maximum uses")
        
        # Increment uses
        return self.invitation_repo.increment_uses(invitation.id)


class ListInvitationsByUnitUseCase:
    """List invitations for a unit."""
    
    def __init__(self, invitation_repo: InvitationRepositoryPort):
        self.invitation_repo = invitation_repo
    
    def execute(self, unit_id: UUID) -> List[Invitation]:
        """List invitations."""
        return self.invitation_repo.get_by_unit(unit_id)


class RevokeInvitationUseCase:
    """Revoke an invitation (delete it)."""
    
    def __init__(self, invitation_repo: InvitationRepositoryPort):
        self.invitation_repo = invitation_repo
    
    def execute(self, invitation_id: UUID) -> bool:
        """Revoke invitation."""
        invitation = self.invitation_repo.get_by_id(invitation_id)
        if not invitation:
            raise InvitationNotFoundError(f"Invitation {invitation_id} not found")
        
        return self.invitation_repo.delete(invitation_id)
