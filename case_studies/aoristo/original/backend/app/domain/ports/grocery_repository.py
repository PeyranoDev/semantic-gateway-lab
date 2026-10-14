"""
Grocery Repository Port (Interface).
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.grocery import Grocery


class GroceryRepositoryPort(ABC):
    """Abstract interface for Grocery persistence operations."""

    @abstractmethod
    def get_by_id(self, grocery_id: int) -> Optional[Grocery]:
        """Get grocery by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[Grocery]:
        """Get all groceries."""
        pass

    @abstractmethod
    def create(self, grocery: Grocery) -> Grocery:
        """Create grocery."""
        pass

    @abstractmethod
    def update(self, grocery: Grocery) -> Grocery:
        """Update grocery."""
        pass

    @abstractmethod
    def delete(self, grocery_id: int) -> bool:
        """Soft delete grocery."""
        pass
