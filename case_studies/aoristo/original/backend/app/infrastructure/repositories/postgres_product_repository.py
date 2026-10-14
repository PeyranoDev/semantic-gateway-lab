"""
PostgreSQL Product Repository implementation.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.domain.entities.product import Product
from app.domain.models.product import Product as ProductModel
from app.domain.ports.product_repository import ProductRepositoryPort


class PostgresProductRepository(ProductRepositoryPort):
    """PostgreSQL implementation of ProductRepositoryPort."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_entity(model: ProductModel) -> Product:
        return Product(Id=model.Id, Name=model.Name)

    @staticmethod
    def _apply_entity(model: ProductModel, entity: Product) -> ProductModel:
        model.Name = entity.Name
        return model

    def create(self, product: Product) -> Product:
        """Create product."""
        model = ProductModel(Name=product.Name)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        model = self.db.query(ProductModel).filter(ProductModel.Id == product_id).first()
        return self._to_entity(model) if model else None
    
    def get_by_name(self, name: str) -> Optional[Product]:
        """Get product by name (case-insensitive exact match)."""
        model = self.db.query(ProductModel).filter(ProductModel.Name.ilike(name)).first()
        return self._to_entity(model) if model else None

    def get_all(self) -> List[Product]:
        """Get all products (global catalog)."""
        return [self._to_entity(model) for model in self.db.query(ProductModel).all()]

    def get_by_category_id(self, category_id: int) -> List[Product]:
        """Get products by category."""
        # Product model is global and has no CategoryId. 
        # Categories are in InventoryItems. 
        # For now return empty list to satisfy interface and assume lookup is done via Inventory.
        return []



    def update(self, product: Product) -> Product:
        """Update product."""
        model = self.db.query(ProductModel).filter(ProductModel.Id == product.Id).first()
        if not model:
            return product
        self._apply_entity(model, product)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, product_id: int) -> bool:
        """Delete product."""
        model = self.db.query(ProductModel).filter(ProductModel.Id == product_id).first()
        if model:
            self.db.delete(model)
            self.db.commit()
            return True
        return False
