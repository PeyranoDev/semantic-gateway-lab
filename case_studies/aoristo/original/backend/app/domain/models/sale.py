"""
Sale and SaleItem models.
Matches .NET Domain/Entities/Sale.cs and SaleItem.cs
"""
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from app.domain.models.base import Base
from app.domain.enums import SaleStatus


class Sale(Base):
    """Sales transaction entity."""
    __tablename__ = "Sales"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Date = Column(DateTime, nullable=False, default=datetime.utcnow)
    Subtotal = Column(Numeric(18, 2), nullable=False, default=0)
    Discount = Column(Numeric(18, 2), nullable=False, default=0)
    DiscountPercent = Column(Numeric(5, 2), nullable=True)
    Total = Column(Numeric(18, 2), nullable=False)
    PaymentMethod = Column(String(50), nullable=True)
    Status = Column(String(20), nullable=False, default=SaleStatus.COMPLETED.value)
    MpPaymentId = Column(String(100), nullable=True)
    
    # Foreign keys
    UserId = Column(UUID(as_uuid=True), ForeignKey("Users.Id"), nullable=False)
    GroceryId = Column(Integer, ForeignKey("Groceries.Id"), nullable=False)

    # Relationships
    User = relationship("User")
    Grocery = relationship("Grocery", back_populates="Sales")
    Items = relationship("SaleItem", back_populates="Sale", cascade="all, delete-orphan")
    Promotions = relationship("SalePromotion", back_populates="Sale", cascade="all, delete-orphan")


class SaleItem(Base):
    """Individual items in a sale."""
    __tablename__ = "SaleItems"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    SaleId = Column(Integer, ForeignKey("Sales.Id"), nullable=False)
    ProductId = Column(Integer, ForeignKey("Products.Id"), nullable=False)
    ProductName = Column(String(200), nullable=False)
    Quantity = Column(Numeric(10, 3), nullable=False)
    UnitPrice = Column(Numeric(18, 2), nullable=False)
    Subtotal = Column(Numeric(18, 2), nullable=False)

    # Relationships
    Sale = relationship("Sale", back_populates="Items")
    Product = relationship("Product")


class SalePromotion(Base):
    """Promotions applied to a sale."""
    __tablename__ = "SalePromotions"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    SaleId = Column(Integer, ForeignKey("Sales.Id"), nullable=False)
    PromotionId = Column(Integer, ForeignKey("Promotions.Id"), nullable=True)
    PromotionName = Column(String(200), nullable=False)
    DiscountAmount = Column(Numeric(18, 2), nullable=False)
    DiscountPercent = Column(Numeric(5, 2), nullable=True)
    PromotionType = Column(String(50), nullable=True)

    # Relationships
    Sale = relationship("Sale", back_populates="Promotions")
