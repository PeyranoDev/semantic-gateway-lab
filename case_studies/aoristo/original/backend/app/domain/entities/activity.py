"""Activity domain entity and constants."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.domain.entities.user import User


class ActivityImportance:
    """Activity importance levels for role-based filtering."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActivityType:
    """Activity type constants."""
    SALE = "Venta"
    PURCHASE = "Compra"
    INVENTORY = "Inventario"
    USER = "Usuario"
    PRODUCT = "Producto"
    SUPPLIER = "Proveedor"
    AUTH = "Autenticación"
    SYSTEM = "Sistema"


@dataclass
class Activity:
    Id: Optional[int]
    Type: str
    Action: str
    EntityType: Optional[str]
    EntityId: Optional[str]
    Detail: Optional[str]
    Importance: str
    CreatedAt: datetime
    UserId: Optional[UUID]
    GroceryId: Optional[int]
    User: Optional[User] = None
