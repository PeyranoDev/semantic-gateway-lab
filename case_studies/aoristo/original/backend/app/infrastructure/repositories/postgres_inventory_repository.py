"""
PostgreSQL Inventory Repository implementation.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.domain.entities.inventory import InventoryItem
from app.domain.entities.product import Product
from app.domain.entities.category import Category
from app.domain.models.inventory import InventoryItem as InventoryItemModel
from app.domain.models.product import Product as ProductModel
from app.domain.models.category import Category as CategoryModel
from app.domain.ports.inventory_repository import InventoryRepositoryPort


class PostgresInventoryRepository(InventoryRepositoryPort):
    """PostgreSQL implementation of InventoryRepositoryPort."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _product_to_entity(model: ProductModel | None) -> Product | None:
        if not model:
            return None
        return Product(Id=model.Id, Name=model.Name)

    @staticmethod
    def _category_to_entity(model: CategoryModel | None) -> Category | None:
        if not model:
            return None
        return Category(
            Id=model.Id,
            Name=model.Name,
            Description=model.Description,
            GroceryId=model.GroceryId,
        )

    def _to_entity(self, model: InventoryItemModel) -> InventoryItem:
        return InventoryItem(
            Id=model.Id,
            ProductId=model.ProductId,
            GroceryId=model.GroceryId,
            CategoryId=model.CategoryId,
            Stock=model.Stock,
            SalePrice=float(model.SalePrice) if model.SalePrice is not None else 0.0,
            LastPurchasePrice=float(model.LastPurchasePrice) if model.LastPurchasePrice is not None else None,
            Unit=model.Unit,
            MinStock=model.MinStock,
            MaxStock=model.MaxStock,
            LastUpdated=model.LastUpdated,
            Product=self._product_to_entity(getattr(model, "Product", None)),
            Category=self._category_to_entity(getattr(model, "Category", None)),
            Grocery=None,
        )

    @staticmethod
    def _apply_entity(model: InventoryItemModel, entity: InventoryItem) -> InventoryItemModel:
        model.ProductId = entity.ProductId
        model.GroceryId = entity.GroceryId
        model.CategoryId = entity.CategoryId
        model.Stock = entity.Stock
        model.SalePrice = entity.SalePrice
        model.LastPurchasePrice = entity.LastPurchasePrice
        model.Unit = entity.Unit
        model.MinStock = entity.MinStock
        model.MaxStock = entity.MaxStock
        return model

    def create(self, item: InventoryItem) -> InventoryItem:
        """Create inventory item."""
        model = InventoryItemModel(
            ProductId=item.ProductId,
            GroceryId=item.GroceryId,
            CategoryId=item.CategoryId,
            Stock=item.Stock,
            SalePrice=item.SalePrice,
            LastPurchasePrice=item.LastPurchasePrice,
            Unit=item.Unit,
            MinStock=item.MinStock,
            MaxStock=item.MaxStock,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, item_id: int) -> Optional[InventoryItem]:
        """Get item by ID with product and category loaded."""
        model = (
            self.db.query(InventoryItemModel)
            .options(
                joinedload(InventoryItemModel.Product),
                joinedload(InventoryItemModel.Category)
            )
            .filter(InventoryItemModel.Id == item_id)
            .first()
        )
        return self._to_entity(model) if model else None

    def get_by_product_id(self, product_id: int, grocery_id: int) -> Optional[InventoryItem]:
        """Get item by product and grocery."""
        model = (
            self.db.query(InventoryItemModel)
            .filter(
                InventoryItemModel.ProductId == product_id,
                InventoryItemModel.GroceryId == grocery_id
            )
            .first()
        )
        return self._to_entity(model) if model else None

    def get_all(self, grocery_id: int) -> List[InventoryItem]:
        """Get all items for grocery with product and category loaded."""
        return [
            self._to_entity(model)
            for model in (
                self.db.query(InventoryItemModel)
                .options(
                    joinedload(InventoryItemModel.Product),
                    joinedload(InventoryItemModel.Category)
                )
                .filter(InventoryItemModel.GroceryId == grocery_id)
                .all()
            )
        ]

    def get_low_stock(self, grocery_id: int, threshold: int = 10) -> List[InventoryItem]:
        """Get items with stock below threshold."""
        return [
            self._to_entity(model)
            for model in (
                self.db.query(InventoryItemModel)
                .options(
                    joinedload(InventoryItemModel.Product),
                    joinedload(InventoryItemModel.Category)
                )
                .filter(
                    InventoryItemModel.GroceryId == grocery_id,
                    InventoryItemModel.Stock <= threshold,
                    InventoryItemModel.Stock > 0
                )
                .all()
            )
        ]

    def get_out_of_stock(self, grocery_id: int) -> List[InventoryItem]:
        """Get items with zero stock."""
        return [
            self._to_entity(model)
            for model in (
                self.db.query(InventoryItemModel)
                .options(
                    joinedload(InventoryItemModel.Product),
                    joinedload(InventoryItemModel.Category)
                )
                .filter(
                    InventoryItemModel.GroceryId == grocery_id,
                    InventoryItemModel.Stock <= 0
                )
                .all()
            )
        ]

    def update(self, item: InventoryItem) -> InventoryItem:
        """Update inventory item."""
        model = self.db.query(InventoryItemModel).filter(InventoryItemModel.Id == item.Id).first()
        if not model:
            return item
        self._apply_entity(model, item)
        model.LastUpdated = datetime.utcnow()
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def adjust_stock(self, item_id: int, new_stock: int) -> InventoryItem:
        """Adjust stock for item."""
        model = self.db.query(InventoryItemModel).filter(InventoryItemModel.Id == item_id).first()
        if model:
            model.Stock = new_stock
            model.LastUpdated = datetime.utcnow()
            self.db.commit()
            self.db.refresh(model)
            return self._to_entity(model)
        return None

    def delete(self, item_id: int | InventoryItem | InventoryItemModel) -> bool:
        """Delete inventory item."""
        resolved_id = item_id
        if isinstance(item_id, InventoryItemModel):
            resolved_id = item_id.Id
        elif isinstance(item_id, InventoryItem):
            resolved_id = item_id.Id
        else:
            resolved_id = getattr(item_id, "Id", getattr(item_id, "id", item_id))

        model = self.db.query(InventoryItemModel).filter(InventoryItemModel.Id == resolved_id).first()
        if model:
            self.db.delete(model)
            self.db.commit()
            return True
        return False
