"""
Product Repository Port (Interface).
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.product import Product


class ProductRepositoryPort(ABC):
    """Abstract interface for Product persistence operations."""

    @abstractmethod
    def create(self, product: Product) -> Product:
        """Create a new product."""
        pass

    @abstractmethod
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[Product]:
        """Get product by name (case-insensitive exact match)."""
        pass

    @abstractmethod
    def get_all(self) -> List[Product]:
        """Get all products."""
        pass

    @abstractmethod
    def get_by_category_id(self, category_id: int) -> List[Product]:
        """Get products by category."""
        pass

    @abstractmethod
    def update(self, product: Product) -> Product:
        """Update an existing product."""
        pass

    @abstractmethod
    def delete(self, product_id: int) -> bool:
        """Delete a product."""
        pass
