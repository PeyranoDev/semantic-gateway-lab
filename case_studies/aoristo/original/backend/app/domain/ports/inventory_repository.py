"""
Inventory Repository Port (Interface).
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.inventory import InventoryItem


class InventoryRepositoryPort(ABC):
    """Abstract interface for Inventory persistence operations."""

    @abstractmethod
    def create(self, item: InventoryItem) -> InventoryItem:
        """Create a new inventory item."""
        pass

    @abstractmethod
    def get_by_id(self, item_id: int) -> Optional[InventoryItem]:
        """Get inventory item by ID."""
        pass

    @abstractmethod
    def get_by_product_id(self, product_id: int, grocery_id: int) -> Optional[InventoryItem]:
        """Get inventory item by product ID for a specific grocery."""
        pass

    @abstractmethod
    def get_all(self, grocery_id: int) -> List[InventoryItem]:
        """Get all inventory items for a grocery."""
        pass

    @abstractmethod
    def get_low_stock(self, grocery_id: int, threshold: int = 10) -> List[InventoryItem]:
        """Get items with stock below threshold."""
        pass

    @abstractmethod
    def get_out_of_stock(self, grocery_id: int) -> List[InventoryItem]:
        """Get items with zero stock."""
        pass

    @abstractmethod
    def update(self, item: InventoryItem) -> InventoryItem:
        """Update an existing inventory item."""
        pass

    @abstractmethod
    def adjust_stock(self, item_id: int, new_stock: int) -> InventoryItem:
        """Adjust stock for an item."""
        pass

    @abstractmethod
    def delete(self, item_id: int) -> bool:
        """Delete an inventory item."""
        pass
