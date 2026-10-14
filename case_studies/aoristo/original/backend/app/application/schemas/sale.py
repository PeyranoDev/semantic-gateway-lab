"""
Sale schemas.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class SaleItemRequest(BaseModel):
    """Sale item in create request."""
    productId: int
    productName: str
    quantity: float
    unitPrice: float


class AppliedPromotionRequest(BaseModel):
    promotionId: str
    promotionName: str
    type: str
    discountAmount: float
    discountPercent: Optional[float] = None


class CreateSaleRequest(BaseModel):
    """Request to create sale."""
    items: List[SaleItemRequest]
    paymentMethod: Optional[str] = "efectivo"
    status: Optional[str] = "completed"
    discount: Optional[float] = 0.0
    date: Optional[datetime] = None
    appliedPromotions: Optional[List[AppliedPromotionRequest]] = []


class SaleItemResponse(BaseModel):
    """Sale item in response."""
    productId: int
    productName: str
    quantity: float
    unitPrice: float
    subtotal: float
    
    class Config:
        from_attributes = True


class SaleResponse(BaseModel):
    """Sale response schema."""
    id: int
    date: datetime
    total: float
    subtotal: Optional[float] = None
    discount: Optional[float] = None
    discountPercent: Optional[float] = None
    userId: str
    name: Optional[str] = None
    items: List[SaleItemResponse]
    paymentMethod: Optional[str] = None
    status: Optional[str] = "completed"
    
    class Config:
        from_attributes = True


class PaginatedSalesResponse(BaseModel):
    """Paginated sales response."""
    items: List[SaleResponse]
    page: int
    pageSize: int
    totalCount: int
    totalPages: int
    hasNextPage: bool
    hasPreviousPage: bool
