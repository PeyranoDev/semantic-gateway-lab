"""
Purchase and PurchaseItem models.
Matches .NET Domain/Entities/Purchase.cs and PurchaseItem.cs
"""
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.domain.models.base import Base
from app.domain.enums import PurchaseStatus


class Purchase(Base):
    """Purchase/restock transaction entity."""
    __tablename__ = "Purchases"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Date = Column(DateTime, nullable=False, default=datetime.utcnow)
    SupplierId = Column(String(100), nullable=True)
    SupplierName = Column(String(200), nullable=True)
    Total = Column(Numeric(18, 2), nullable=False)
    Status = Column(String(20), nullable=False, default=PurchaseStatus.RECEIVED.value)
    Notes = Column(String(1000), nullable=True)
    
    # Foreign keys
    GroceryId = Column(Integer, ForeignKey("Groceries.Id"), nullable=False)
 
    # Relationships
    Grocery = relationship("Grocery", back_populates="Purchases")
    Items = relationship("PurchaseItem", back_populates="Purchase", cascade="all, delete-orphan")


class PurchaseItem(Base):
    """Individual items in a purchase."""
    __tablename__ = "PurchaseItems"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    PurchaseId = Column(Integer, ForeignKey("Purchases.Id"), nullable=False)
    ProductId = Column(Integer, ForeignKey("Products.Id"), nullable=False)
    ProductName = Column(String(200), nullable=False)
    Quantity = Column(Numeric(10, 3), nullable=False)
    UnitCost = Column(Numeric(18, 2), nullable=False)
    Subtotal = Column(Numeric(18, 2), nullable=False)

    # Relationships
    Purchase = relationship("Purchase", back_populates="Items")
    Product = relationship("Product")
