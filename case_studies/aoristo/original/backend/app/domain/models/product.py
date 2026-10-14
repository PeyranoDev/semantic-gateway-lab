"""
Product model.
Global product catalog - shared across all groceries.
Only contains the product name. All other details (category, price, stock) are in InventoryItem.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.domain.models.base import Base


class Product(Base):
    """
    Product entity - global product catalog (name only).
    Each grocery has its own inventory with prices, stock, and categories for these products.
    """
    __tablename__ = "Products"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String(200), nullable=False, unique=True, index=True)

    # Relationships
    InventoryItems = relationship("InventoryItem", back_populates="Product")
