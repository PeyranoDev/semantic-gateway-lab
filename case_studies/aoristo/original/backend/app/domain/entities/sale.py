"""Sale domain entities."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from .user import User
from .grocery import Grocery


@dataclass
class SaleItem:
    Id: Optional[int]
    SaleId: Optional[int]
    ProductId: int
    ProductName: str
    Quantity: float
    UnitPrice: float
    Subtotal: float


@dataclass
class SalePromotion:
    Id: Optional[int]
    SaleId: Optional[int]
    PromotionId: Optional[int]
    PromotionName: str
    DiscountAmount: float
    DiscountPercent: Optional[float]
    PromotionType: Optional[str] = None


@dataclass
class Sale:
    Id: Optional[int]
    Date: datetime
    Subtotal: float
    Discount: float
    DiscountPercent: Optional[float]
    Total: float
    PaymentMethod: Optional[str]
    Status: str
    MpPaymentId: Optional[str]
    UserId: UUID
    GroceryId: int
    Items: List[SaleItem] = field(default_factory=list)
    Promotions: List[SalePromotion] = field(default_factory=list)
    User: Optional[User] = None
    Grocery: Optional[Grocery] = None
