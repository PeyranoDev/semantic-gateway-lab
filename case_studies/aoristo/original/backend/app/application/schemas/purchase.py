"""
Purchase schemas.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class PurchaseItemRequest(BaseModel):
    """Purchase item in request."""
    productId: Optional[int] = None  # None if new product
    productName: str
    categoryId: int  # Required for inventory
    quantity: float
    unitCost: float
    subtotal: Optional[float] = None


class CreatePurchaseRequest(BaseModel):
    """Request to create purchase."""
    supplierId: Optional[str] = None
    supplierName: Optional[str] = None
    items: List[PurchaseItemRequest]
    notes: Optional[str] = None


class UpdatePurchaseRequest(BaseModel):
    """Request to update purchase."""
    supplierId: Optional[str] = None
    supplierName: Optional[str] = None
    items: Optional[List[PurchaseItemRequest]] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class PurchaseItemResponse(BaseModel):
    """Purchase item response."""
    productId: int
    productName: str
    quantity: float
    unitCost: float
    subtotal: float
    
    class Config:
        from_attributes = True


class PurchaseResponse(BaseModel):
    """Purchase response."""
    id: int
    date: datetime
    supplierId: Optional[str] = None
    supplierName: Optional[str] = None
    total: float
    status: str
    notes: Optional[str] = None
    items: List[PurchaseItemResponse]
    
    
    class Config:
        from_attributes = True


class PaginatedPurchasesResponse(BaseModel):
    """Paginated response for purchases."""
    items: List[PurchaseResponse]
    page: int
    pageSize: int
    totalCount: int
    totalPages: int
    hasNextPage: bool
    hasPreviousPage: bool
