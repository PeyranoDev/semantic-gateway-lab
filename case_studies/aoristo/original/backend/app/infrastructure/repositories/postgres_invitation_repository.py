"""
PostgreSQL Invitation Repository implementation.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.domain.entities.redvecina import Invitation
from app.domain.models.redvecina import Invitation as InvitationModel


class PostgresInvitationRepository:
    """PostgreSQL implementation for Invitation repository."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_entity(model: InvitationModel) -> Invitation:
        return Invitation(
            id=model.Id,
            unit_id=model.UnitId,
            token=model.Token,
            current_uses=model.CurrentUses,
            max_uses=model.MaxUses,
            expires_at=model.ExpiresAt,
            created_at=model.CreatedAt,
        )

    def create(self, invitation: Invitation) -> Invitation:
        """Create invitation."""
        model = InvitationModel(
            UnitId=invitation.unit_id,
            Token=invitation.token,
            CurrentUses=invitation.current_uses,
            MaxUses=invitation.max_uses,
            ExpiresAt=invitation.expires_at,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, invitation_id: UUID) -> Optional[Invitation]:
        """Get invitation by ID."""
        model = self.db.query(InvitationModel).filter(InvitationModel.Id == invitation_id).first()
        return self._to_entity(model) if model else None

    def get_by_token(self, token: str) -> Optional[Invitation]:
        """Get invitation by token."""
        model = self.db.query(InvitationModel).filter(InvitationModel.Token == token).first()
        return self._to_entity(model) if model else None

    def get_by_unit(self, unit_id: UUID) -> List[Invitation]:
        """Get all invitations for a unit."""
        models = self.db.query(InvitationModel).filter(InvitationModel.UnitId == unit_id).all()
        return [self._to_entity(model) for model in models]

    def increment_uses(self, invitation_id: UUID) -> Optional[Invitation]:
        """Increment invitation uses counter."""
        model = self.db.query(InvitationModel).filter(InvitationModel.Id == invitation_id).first()
        if not model:
            return None
        
        model.CurrentUses += 1
        
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def update(self, invitation: Invitation) -> Invitation:
        """Update invitation."""
        model = self.db.query(InvitationModel).filter(InvitationModel.Id == invitation.id).first()
        if not model:
            raise ValueError(f"Invitation with id {invitation.id} not found")
        
        model.CurrentUses = invitation.current_uses
        model.MaxUses = invitation.max_uses
        model.ExpiresAt = invitation.expires_at
        
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, invitation_id: UUID) -> bool:
        """Delete invitation."""
        model = self.db.query(InvitationModel).filter(InvitationModel.Id == invitation_id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True
