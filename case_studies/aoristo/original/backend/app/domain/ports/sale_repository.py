"""
Sale Repository Port (Interface).
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import datetime
from app.domain.entities.sale import Sale


class SaleRepositoryPort(ABC):
    """Abstract interface for Sale persistence operations."""

    @abstractmethod
    def create(self, sale: Sale) -> Sale:
        """Create a new sale with items."""
        pass

    @abstractmethod
    def get_by_id(self, sale_id: int) -> Optional[Sale]:
        """Get sale by ID with items."""
        pass

    @abstractmethod
    def get_all(
        self, 
        grocery_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[Sale]:
        """Get all sales for a grocery, optionally filtered by date range."""
        pass

    @abstractmethod
    def get_paginated(
        self,
        grocery_id: int,
        page: int,
        page_size: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Sale], int]:
        """Get paginated sales. Returns (items, total_count)."""
        pass

    @abstractmethod
    def get_today_stats(self, grocery_id: int) -> dict:
        """Get today's sales statistics."""
        pass

    @abstractmethod
    def update(self, sale: Sale) -> Sale:
        """Update sale status."""
        pass
