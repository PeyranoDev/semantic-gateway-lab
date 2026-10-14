"""
API Dependencies - Authentication and authorization.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from uuid import UUID

from app.config import settings
from app.infrastructure.database import get_db
from app.infrastructure.repositories import PostgresUserRepository
from app.domain.enums import GroceryRole
import logging

logger = logging.getLogger(__name__)


security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordHasher:
    """Password hashing utility."""
    
    def hash(self, password: str) -> str:
        return pwd_context.hash(password)
    
    def verify(self, password: str, hashed: str) -> bool:
        return pwd_context.verify(password, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience
    })
    
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer
        )
        return payload
    except JWTError as e:
        logger.error(f"JWT Validation Error (Strict): {str(e)}")
        # Try with relaxed validation for RedVecina tokens
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.jwt_algorithm],
                options={"verify_aud": False, "verify_iss": False}
            )
            logger.info("JWT validated with relaxed options (RedVecina token)")
            return payload
        except JWTError as e2:
            logger.error(f"JWT Validation Error (Relaxed): {str(e2)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token inválido o expirado: {str(e2)}"
            )


class CurrentUser:
    """Current authenticated user data."""
    def __init__(
        self,
        id: str | int,
        email: str,
        name: str,
        role: int,
        grocery_id: Optional[int],
        building_id: Optional[str] = None,
        unit_id: Optional[str] = None,
        redvecina_role: Optional[str] = None,
    ):
        self.id = str(id)  # Standardize to string internally
        self.email = email
        self.name = name
        self.role = role
        self.grocery_id = grocery_id
        self.building_id = building_id
        self.unit_id = unit_id
        self.redvecina_role = redvecina_role
        # logger.error(f"CurrentUser Init: {id}, Role={role}, IsSA={self.is_super_admin}")

    @property
    def user_id(self) -> str:
        """
        Backwards-compatible alias.
        Some RedVecina routes still reference `current_user.user_id`.
        """
        try:
            return UUID(str(self.id))
        except Exception:
            return self.id
    
    @property
    def is_super_admin(self) -> bool:
        return self.role == GroceryRole.SUPER_ADMIN.value
    
    @property
    def is_admin(self) -> bool:
        return self.role in (GroceryRole.ADMIN.value, GroceryRole.SUPER_ADMIN.value)

    @property
    def redvecina_role_normalized(self) -> str:
        return (self.redvecina_role or "").strip().lower()

    @property
    def is_redvecina_staff(self) -> bool:
        return self.redvecina_role_normalized in ("admin", "staff")

    @property
    def is_redvecina_resident(self) -> bool:
        # Treat tenant as resident for authorization purposes.
        return self.redvecina_role_normalized in ("resident", "residente", "tenant")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    Dependency to get current authenticated user from JWT.
    Handles both Verdusoft (integer ID) and RedVecina (UUID) tokens.
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    # Extract user info from token
    user_id = payload.get("sub") or payload.get("userId") or payload.get("id")

    # DEBUG LOGGING (moved to top to catch all cases)
    token_role_debug = payload.get("role")
    logger.error(f"DEBUG AUTH: Payload keys: {list(payload.keys())}")
    logger.error(f"DEBUG AUTH: UserID: {user_id}, Raw Role: {token_role_debug} (Type: {type(token_role_debug)})")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no contiene información de usuario"
        )
    
    # Check if user_id is a UUID (RedVecina) or integer (Verdusoft)
    is_uuid = False
    try:
        int(user_id)
    except ValueError:
        is_uuid = True
    
    # Only try DB lookup for Verdusoft integer IDs
    # Update: Now we lookup by UUID or Int (legacy transition)
    user_repo = PostgresUserRepository(db)
    
    # Try to resolve user by ID (handling str/uuid)
    # Since we are mid-migration, user_id might be int or uuid string
    user = user_repo.get_by_id(user_id)
    
    if user:
        # Load Role/Grocery from VerdusoftProfile
        # TODO: In future, we might load RedVecinaProfile too depending on context
        
        resolved_role = GroceryRole.STAFF.value
        grocery_id = None
        building_id = None
        unit_id = None
        redvecina_role = None
        
        if user.VerdusoftProfile:
            resolved_role = user.VerdusoftProfile.Role or GroceryRole.STAFF.value
            grocery_id = user.VerdusoftProfile.GroceryId

        if user.RedVecinaProfile:
            building_id = str(user.RedVecinaProfile.BuildingId) if user.RedVecinaProfile.BuildingId else None
            unit_id = str(user.RedVecinaProfile.UnitId) if user.RedVecinaProfile.UnitId else None
            redvecina_role = user.RedVecinaProfile.Role
        
        # Check for Global SuperAdmin
        if user.IsGlobalSuperAdmin:
            resolved_role = GroceryRole.SUPER_ADMIN.value
            logger.error(f"DEBUG AUTH: User {user.Id} is GlobalSuperAdmin via DB.")
        else:
            logger.error(f"DEBUG AUTH: User {user.Id} is NOT GlobalSuperAdmin via DB (Val: {user.IsGlobalSuperAdmin}). Profile Role: {resolved_role}")

        return CurrentUser(
            id=str(user.Id), # Return as string standard
            email=user.Email,
            name=user.Name,
            role=resolved_role,
            grocery_id=grocery_id,
            building_id=building_id,
            unit_id=unit_id,
            redvecina_role=redvecina_role,
        )
    
    # Fallback to token data (If DB lookup failed but token is valid - e.g. cross-domain temp)
    token_role = payload.get("role", GroceryRole.STAFF.value)
    if isinstance(token_role, str):
         # ... existing string parsing logic is fine for fallback
         pass 

    # Simplify fallback return
    fallback_role = payload.get("role")
    fallback_redvecina_role: Optional[str] = fallback_role if isinstance(fallback_role, str) else None
    return CurrentUser(
        id=str(user_id),
        email=payload.get("email", ""),
        name=payload.get("name", payload.get("full_name", "")),
        role=int(token_role) if isinstance(token_role, (int, float)) else GroceryRole.STAFF.value, 
        grocery_id=int(payload.get("groceryId")) if payload.get("groceryId") else None,
        building_id=payload.get("buildingId"),
        unit_id=payload.get("unitId"),
        redvecina_role=fallback_redvecina_role,
    )


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Require Admin or SuperAdmin role."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de Admin o SuperAdmin"
        )
    return current_user


def require_super_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Require SuperAdmin role."""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de SuperAdmin"
        )
    return current_user


def get_tenant_grocery_id(
    current_user: CurrentUser = Depends(get_current_user),
    x_grocery_id: Optional[int] = Header(None, alias="X-Grocery-Id")
) -> int:
    """
    Get the current grocery ID for multi-tenant operations.
    SuperAdmin can specify a grocery via X-Grocery-Id header.
    """
    if current_user.grocery_id:
        return current_user.grocery_id
    
    # SuperAdmin can bypass or specify via header
    if current_user.is_super_admin:
        if x_grocery_id:
            return x_grocery_id
        # Default to 1 (main grocery) for SuperAdmin if not specified
        # This prevents crashes in dashboards when SuperAdmin is browsing
        return 1
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Usuario no tiene verdulería asignada"
    )
