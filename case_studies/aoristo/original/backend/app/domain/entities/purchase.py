"""Purchase domain entities."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class PurchaseItem:
    Id: Optional[int]
    PurchaseId: Optional[int]
    ProductId: int
    ProductName: str
    Quantity: float
    UnitCost: float
    Subtotal: float


@dataclass
class Purchase:
    Id: Optional[int]
    Date: datetime
    SupplierId: Optional[str]
    SupplierName: Optional[str]
    Total: float
    Status: str
    Notes: Optional[str]
    GroceryId: int
    Items: List[PurchaseItem] = field(default_factory=list)
