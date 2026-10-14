"""
Common response schemas.
"""
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: List[T]
    page: int
    pageSize: int
    totalCount: int
    totalPages: int
    hasNextPage: bool
    hasPreviousPage: bool
