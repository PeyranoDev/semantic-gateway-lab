"""
User Profiles for Modular Monolith.
Separates application-specific user data from the core Global User.
"""
import uuid
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from typing import Optional

from app.domain.models.base import Base
from app.domain.enums import GroceryRole


class VerdusoftProfile(Base):
    """
    Profile for Verdusoft (Retail/ERP) users.
    Links a Global User to a specific Grocery Store.
    """
    __tablename__ = "VerdusoftProfiles"

    Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    UserId = Column(UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=False, unique=True)
    GroceryId = Column(Integer, ForeignKey("Groceries.Id"), nullable=True)
    Role = Column(Integer, nullable=True)  # GroceryRole enum value

    # Relationships
    User = relationship("User", back_populates="VerdusoftProfile")
    Grocery = relationship("Grocery", back_populates="VerdusoftProfiles")

    @property
    def role_enum(self) -> Optional[GroceryRole]:
        """Get role as enum."""
        if self.Role is None:
            return None
        return GroceryRole(self.Role)


class RedVecinaProfile(Base):
    """
    Profile for RedVecina (Consortium/Residential) users.
    Links a Global User to a specific Residential Unit (Department/House).
    """
    __tablename__ = "RedVecinaProfiles"

    Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    UserId = Column(UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=False, unique=True)
    
    # RedVecina specific fields
    UnitId = Column(UUID(as_uuid=True), ForeignKey("Units.Id"), nullable=True)
    BuildingId = Column(UUID(as_uuid=True), ForeignKey("Buildings.Id"), nullable=True)
    
    Role = Column(String(50), default="resident") # 'admin' | 'resident' | 'tenant' | 'staff'

    # Relationships
    User = relationship("User", back_populates="RedVecinaProfile")
    Unit = relationship("Unit", back_populates="Profiles")
    Building = relationship("Building", back_populates="Profiles")
