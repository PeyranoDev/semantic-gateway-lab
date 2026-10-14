"""
Grocery (Verdulería) model.
Matches .NET Domain/Entities/Grocery.cs
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from app.domain.models.base import Base


class Grocery(Base):
    """
    Grocery store entity (Verdulería).
    Multi-tenant: each grocery is a separate tenant.
    """
    __tablename__ = "Groceries"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String(200), nullable=False)
    Address = Column(String(500), nullable=True)
    Phone = Column(String(50), nullable=True)
    Email = Column(String(200), nullable=True)
    IsActive = Column(Boolean, default=True, nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow, nullable=False)
    UpdatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    VerdusoftProfiles = relationship("VerdusoftProfile", back_populates="Grocery")
    Categories = relationship("Category", back_populates="Grocery")
    InventoryItems = relationship("InventoryItem", back_populates="Grocery")
    Sales = relationship("Sale", back_populates="Grocery")
    Purchases = relationship("Purchase", back_populates="Grocery")

