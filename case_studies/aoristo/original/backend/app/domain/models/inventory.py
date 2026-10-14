"""
InventoryItem model.
Grocery-specific stock, pricing, and categorization.
"""
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.domain.models.base import Base


class InventoryItem(Base):
    """
    Inventory item - grocery-specific stock, pricing, and category.
    Each grocery has its own inventory with custom prices and categories.
    """
    __tablename__ = "InventoryItems"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    ProductId = Column(Integer, ForeignKey("Products.Id"), nullable=False)
    GroceryId = Column(Integer, ForeignKey("Groceries.Id"), nullable=False)
    CategoryId = Column(Integer, ForeignKey("Categories.Id"), nullable=False)
    Stock = Column(Integer, nullable=False, default=0)
    SalePrice = Column(Numeric(18, 2), nullable=False)
    LastPurchasePrice = Column(Numeric(18, 2), nullable=True)
    Unit = Column(String(20), nullable=True, default="u")  # u, kg, l, etc.
    MinStock = Column(Integer, nullable=True, default=5)
    MaxStock = Column(Integer, nullable=True, default=100)
    LastUpdated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    Product = relationship("Product", back_populates="InventoryItems")
    Grocery = relationship("Grocery", back_populates="InventoryItems")
    Category = relationship("Category", back_populates="InventoryItems")
