"""
User model.
Matches .NET Domain/Entities/User.cs
"""
import uuid
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.domain.models.base import Base
from app.domain.enums import GroceryRole


class User(Base):
    """
    User entity.
    Table name matches EF Core naming: "Users"
    """
    __tablename__ = "Users"

    # Core Identity Fields only
    Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Name = Column(String(100), nullable=False)
    Email = Column(String(255), nullable=False, unique=True)
    PasswordHash = Column(String(255), nullable=False)
    IsActive = Column(Boolean, default=True, nullable=False)
    
    # Platform Role (Optional, for System Superadmins independent of apps)
    IsGlobalSuperAdmin = Column(Boolean, default=False)

    # Modular Relationships
    # uselist=False ensures 1:1 relationship
    VerdusoftProfile = relationship("VerdusoftProfile", back_populates="User", uselist=False, cascade="all, delete-orphan")
    RedVecinaProfile = relationship("RedVecinaProfile", back_populates="User", uselist=False, cascade="all, delete-orphan")
