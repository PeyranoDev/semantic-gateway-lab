"""Inventory domain entity."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.domain.entities.product import Product
from app.domain.entities.category import Category
from app.domain.entities.grocery import Grocery


@dataclass
class InventoryItem:
    Id: Optional[int]
    ProductId: int
    GroceryId: int
    CategoryId: Optional[int]
    Stock: int
    SalePrice: float
    LastPurchasePrice: Optional[float]
    Unit: Optional[str]
    MinStock: Optional[int]
    MaxStock: Optional[int]
    LastUpdated: Optional[datetime]
    Product: Optional[Product] = None
    Category: Optional[Category] = None
    Grocery: Optional[Grocery] = None
