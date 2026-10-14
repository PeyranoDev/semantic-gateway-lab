"""
Activity model for audit trail.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from app.domain.models.base import Base


class ActivityImportance:
    """Activity importance levels for role-based filtering."""
    LOW = "low"           # Visible to all (view inventory, searches)
    MEDIUM = "medium"     # Visible to all (sales, purchases, stock adjustments)
    HIGH = "high"         # Admin only (user created, price changed)
    CRITICAL = "critical" # Admin only (user deleted, role changed)


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


class Activity(Base):
    """Activity audit trail entity."""
    __tablename__ = "Activities"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Type = Column(String(50), nullable=False)          # ActivityType
    Action = Column(String(500), nullable=False)       # Human-readable description
    EntityType = Column(String(50), nullable=True)     # "Sale", "Purchase", "Product", "User", etc.
    EntityId = Column(String(50), nullable=True)       # ID of the affected entity
    Detail = Column(Text, nullable=True)               # JSON with additional details
    Importance = Column(String(20), nullable=False, default=ActivityImportance.MEDIUM)
    CreatedAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Foreign keys
    UserId = Column(UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=True)  # User who performed the action
    GroceryId = Column(Integer, ForeignKey("Groceries.Id"), nullable=True)

    # Relationships
    User = relationship("User", foreign_keys=[UserId])
    Grocery = relationship("Grocery")
