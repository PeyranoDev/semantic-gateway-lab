"""
Invitation Link API routes.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.application.schemas.invitation import (
    InvitationCreate, InvitationResponse,
    ValidateInvitationRequest, ValidateInvitationResponse
)
from app.application.schemas import ApiResponse
from app.infrastructure.api.dependencies import get_current_user, CurrentUser
from app.infrastructure.api.dependencies.service_guards import require_redvecina_user
from app.infrastructure.repositories.postgres_invitation_repository import PostgresInvitationRepository
from app.infrastructure.repositories.postgres_building_repository import PostgresUnitRepository
from app.application.use_cases.invitation import (
    GenerateInvitationUseCase, ValidateInvitationUseCase,
    ListInvitationsByUnitUseCase, RevokeInvitationUseCase,
    InvitationNotFoundError, InvitationExpiredError, InvitationExhaustedError
)

router = APIRouter(prefix="/RedVecina/Invitations", tags=["redvecina-invitations"])


@router.post("", response_model=ApiResponse[InvitationResponse], status_code=status.HTTP_201_CREATED)
def generate_invitation(
    data: InvitationCreate,
    current_user: CurrentUser = Depends(require_redvecina_user),
    db: Session = Depends(get_db)
):
    """Generate invitation link for new residents."""
    invitation_repo = PostgresInvitationRepository(db)
    unit_repo = PostgresUnitRepository(db)
    use_case = GenerateInvitationUseCase(invitation_repo, unit_repo)
    
    try:
        invitation = use_case.execute(data.UnitId, data.MaxUses, data.ValidDays)
        return ApiResponse(
            success=True,
            message="Invitation generated successfully",
            data=InvitationResponse.model_validate(invitation)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/validate", response_model=ApiResponse[ValidateInvitationResponse])
def validate_invitation(
    data: ValidateInvitationRequest,
    db: Session = Depends(get_db)
):
    """Validate and consume invitation (public endpoint for registration)."""
    invitation_repo = PostgresInvitationRepository(db)
    use_case = ValidateInvitationUseCase(invitation_repo)
    
    try:
        invitation = use_case.execute(data.Token)
        response_data = ValidateInvitationResponse(
            Id=invitation.id,
            UnitId=invitation.unit_id,
            CurrentUses=invitation.current_uses,
            MaxUses=invitation.max_uses,
            ExpiresAt=invitation.expires_at,
            IsValid=True,
            Message="Invitation is valid"
        )
        return ApiResponse(success=True, data=response_data)
    except InvitationNotFoundError:
        raise HTTPException(status_code=404, detail="Invitation not found")
    except InvitationExpiredError:
        raise HTTPException(status_code=400, detail="Invitation has expired")
    except InvitationExhaustedError:
        raise HTTPException(status_code=400, detail="Invitation has reached maximum uses")


@router.get("", response_model=ApiResponse[List[InvitationResponse]])
def list_invitations(
    unit_id: UUID = Query(...),
    current_user: CurrentUser = Depends(require_redvecina_user),
    db: Session = Depends(get_db)
):
    """List invitations for a unit."""
    invitation_repo = PostgresInvitationRepository(db)
    use_case = ListInvitationsByUnitUseCase(invitation_repo)
    
    invitations = use_case.execute(unit_id)
    
    return ApiResponse(
        success=True,
        data=[InvitationResponse.model_validate(i) for i in invitations]
    )


@router.delete("/{invitation_id}", response_model=ApiResponse[dict])
def revoke_invitation(
    invitation_id: UUID,
    current_user: CurrentUser = Depends(require_redvecina_user),
    db: Session = Depends(get_db)
):
    """Revoke an invitation."""
    invitation_repo = PostgresInvitationRepository(db)
    use_case = RevokeInvitationUseCase(invitation_repo)
    
    try:
        use_case.execute(invitation_id)
        return ApiResponse(
            success=True,
            message="Invitation revoked successfully",
            data={}
        )
    except InvitationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
