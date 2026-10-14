"""
Category model.
Per-grocery categorization system.
"""
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.domain.models.base import Base


class Category(Base):
    """Product category entity - per grocery."""
    __tablename__ = "Categories"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String(100), nullable=False)
    Description = Column(String(500), nullable=True)
    GroceryId = Column(Integer, ForeignKey("Groceries.Id"), nullable=False)

    # Relationships
    Grocery = relationship("Grocery", back_populates="Categories")
    InventoryItems = relationship("InventoryItem", back_populates="Category")
