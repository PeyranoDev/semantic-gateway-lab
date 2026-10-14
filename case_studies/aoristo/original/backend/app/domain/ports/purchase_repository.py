"""
Purchase Repository Port (Interface).
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from datetime import datetime
from app.domain.entities.purchase import Purchase


class PurchaseRepositoryPort(ABC):
    """Abstract interface for Purchase persistence operations."""

    @abstractmethod
    def create(self, purchase: Purchase) -> Purchase:
        """Create a new purchase with items."""
        pass

    @abstractmethod
    def get_by_id(self, purchase_id: int) -> Optional[Purchase]:
        """Get purchase by ID with items."""
        pass

    @abstractmethod
    def get_paginated(
        self,
        grocery_id: int,
        page: int,
        page_size: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[List[Purchase], int]:
        """Get paginated purchases. Returns (items, total_count)."""
        pass

    @abstractmethod
    def update(self, purchase: Purchase) -> Purchase:
        """Update purchase."""
        pass
