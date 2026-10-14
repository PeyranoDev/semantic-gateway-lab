"""
Domain exceptions.
"""
from app.domain.exceptions.base import DomainException
from app.domain.exceptions.auth import (
    AuthException,
    InvalidCredentialsError,
    UserNotFoundError,
    UserInactiveError,
    EmailAlreadyExistsError,
    UnauthorizedError,
)
from app.domain.exceptions.inventory import (
    InventoryException,
    InventoryItemNotFoundError,
    ProductNotFoundError,
    InsufficientStockError,
    InventoryItemAlreadyExistsError,
)
from app.domain.exceptions.sale import (
    SaleException,
    SaleNotFoundError,
)
from app.domain.exceptions.category import (
    CategoryException,
    CategoryNotFoundError,
)

__all__ = [
    # Base
    "DomainException",
    # Auth
    "AuthException",
    "InvalidCredentialsError",
    "UserNotFoundError",
    "UserInactiveError",
    "EmailAlreadyExistsError",
    "UnauthorizedError",
    # Inventory
    "InventoryException",
    "InventoryItemNotFoundError",
    "ProductNotFoundError",
    "InsufficientStockError",
    "InventoryItemAlreadyExistsError",
    # Sale
    "SaleException",
    "SaleNotFoundError",
    # Category
    "CategoryException",
    "CategoryNotFoundError",
]
