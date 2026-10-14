"""
Service-specific guards to ensure users can only access their respective services.
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.repositories import PostgresUserRepository
from app.infrastructure.api.dependencies.auth import get_current_user, CurrentUser
import logging

logger = logging.getLogger(__name__)

REDVECINA_STAFF_ROLES = {"admin", "staff"}


def _normalize_role(role: str | None) -> str:
    return (role or "").strip().lower()


def require_verdusoft_user(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    Require user to have VerdusoftProfile.
    Raises 403 if user does not have VerduSoft access.
    """
    user_repo = PostgresUserRepository(db)
    user = user_repo.get_by_id(current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Check if user has VerduSoft profile
    if not user.VerdusoftProfile:
        logger.warning(
            f"User {current_user.email} (ID: {current_user.id}) attempted to access VerduSoft without profile"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Esta funcionalidad es solo para usuarios de VerduSoft"
        )
    
    logger.debug(f"VerduSoft access granted to user {current_user.email}")
    return current_user


def require_redvecina_user(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    Require user to have RedVecinaProfile.
    Raises 403 if user does not have RedVecina access.
    """
    user_repo = PostgresUserRepository(db)
    user = user_repo.get_by_id(current_user.id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Check if user has RedVecina profile
    if not user.RedVecinaProfile:
        logger.warning(
            f"User {current_user.email} (ID: {current_user.id}) attempted to access RedVecina without profile"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Esta funcionalidad es solo para usuarios de RedVecina"
        )

    # Enrich current_user with RedVecina-specific context for downstream checks.
    current_user.building_id = str(user.RedVecinaProfile.BuildingId) if user.RedVecinaProfile.BuildingId else None
    current_user.unit_id = str(user.RedVecinaProfile.UnitId) if user.RedVecinaProfile.UnitId else None
    current_user.redvecina_role = user.RedVecinaProfile.Role

    logger.debug(f"RedVecina access granted to user {current_user.email}")
    return current_user


def require_redvecina_staff(
    current_user: CurrentUser = Depends(require_redvecina_user),
) -> CurrentUser:
    """
    Require RedVecina user with admin/staff role.
    """
    role = _normalize_role(current_user.redvecina_role)
    if role not in REDVECINA_STAFF_ROLES and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requiere rol de administracion en RedVecina",
        )
    return current_user
