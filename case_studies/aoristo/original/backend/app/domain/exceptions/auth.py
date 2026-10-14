"""
Authentication exceptions.
"""
from app.domain.exceptions.base import DomainException


class AuthException(DomainException):
    """Base authentication exception."""
    pass


class InvalidCredentialsError(AuthException):
    """Invalid username or password."""
    
    def __init__(self, message: str = "Email o contraseña incorrectos."):
        super().__init__(message, "INVALID_CREDENTIALS")


class UserNotFoundError(AuthException):
    """User not found."""
    
    def __init__(self, user_id: int | str | None = None):
        message = f"Usuario {user_id} no encontrado." if user_id else "Usuario no encontrado."
        super().__init__(message, "USER_NOT_FOUND")


class UserInactiveError(AuthException):
    """User account is inactive."""
    
    def __init__(self, user_id: int | str | None = None):
        message = f"Usuario {user_id} no está activo." if user_id else "La cuenta está desactivada."
        super().__init__(message, "USER_INACTIVE")


class EmailAlreadyExistsError(AuthException):
    """Email already registered."""
    
    def __init__(self, email: str):
        super().__init__(f"El email {email} ya está registrado.", "EMAIL_EXISTS")


class UnauthorizedError(AuthException):
    """User not authorized for this action."""
    
    def __init__(self, message: str = "No autorizado para realizar esta acción."):
        super().__init__(message, "UNAUTHORIZED")
