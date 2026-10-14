"""
PostgreSQL Purchase Repository implementation.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.domain.entities.purchase import Purchase, PurchaseItem
from app.domain.models.purchase import Purchase as PurchaseModel
from app.domain.models.purchase import PurchaseItem as PurchaseItemModel
from app.domain.ports.purchase_repository import PurchaseRepositoryPort


class PostgresPurchaseRepository(PurchaseRepositoryPort):
    """PostgreSQL implementation of PurchaseRepositoryPort."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _item_to_entity(model: PurchaseItemModel) -> PurchaseItem:
        return PurchaseItem(
            Id=model.Id,
            PurchaseId=model.PurchaseId,
            ProductId=model.ProductId,
            ProductName=model.ProductName,
            Quantity=float(model.Quantity),
            UnitCost=float(model.UnitCost),
            Subtotal=float(model.Subtotal),
        )

    def _to_entity(self, model: PurchaseModel) -> Purchase:
        return Purchase(
            Id=model.Id,
            Date=model.Date,
            SupplierId=model.SupplierId,
            SupplierName=model.SupplierName,
            Total=float(model.Total),
            Status=model.Status,
            Notes=model.Notes,
            GroceryId=model.GroceryId,
            Items=[self._item_to_entity(item) for item in model.Items] if model.Items else [],
        )

    @staticmethod
    def _apply_entity(model: PurchaseModel, entity: Purchase) -> PurchaseModel:
        model.Date = entity.Date
        model.SupplierId = entity.SupplierId
        model.SupplierName = entity.SupplierName
        model.Total = entity.Total
        model.Status = entity.Status
        model.Notes = entity.Notes
        model.GroceryId = entity.GroceryId
        return model

    def create(self, purchase: Purchase) -> Purchase:
        """Create purchase with items."""
        model = PurchaseModel(
            Date=purchase.Date,
            SupplierId=purchase.SupplierId,
            SupplierName=purchase.SupplierName,
            Total=purchase.Total,
            Status=purchase.Status,
            Notes=purchase.Notes,
            GroceryId=purchase.GroceryId,
        )
        model.Items = [
            PurchaseItemModel(
                ProductId=item.ProductId,
                ProductName=item.ProductName,
                Quantity=item.Quantity,
                UnitCost=item.UnitCost,
                Subtotal=item.Subtotal,
            )
            for item in (purchase.Items or [])
        ]
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, purchase_id: int) -> Optional[Purchase]:
        """Get purchase by ID with items."""
        model = (
            self.db.query(PurchaseModel)
            .options(joinedload(PurchaseModel.Items))
            .filter(PurchaseModel.Id == purchase_id)
            .first()
        )
        return self._to_entity(model) if model else None

    def get_all(
        self,
        grocery_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Purchase]:
        """Get all purchases for grocery with optional date filter."""
        query = (
            self.db.query(PurchaseModel)
            .options(joinedload(PurchaseModel.Items))
            .filter(PurchaseModel.GroceryId == grocery_id)
        )
        
        if start_date:
            query = query.filter(PurchaseModel.Date >= start_date)
        if end_date:
            query = query.filter(PurchaseModel.Date <= end_date)
        
        return [self._to_entity(model) for model in query.order_by(PurchaseModel.Date.desc()).all()]

    def get_paginated(
        self,
        grocery_id: int,
        page: int,
        page_size: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[List[Purchase], int]:
        """Get paginated purchases. Returns (items, total_count)."""
        from typing import Tuple
        query = (
            self.db.query(PurchaseModel)
            .filter(PurchaseModel.GroceryId == grocery_id)
        )
        
        if start_date:
            query = query.filter(PurchaseModel.Date >= start_date)
        if end_date:
            query = query.filter(PurchaseModel.Date <= end_date)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        purchases = (
            query
            .options(joinedload(PurchaseModel.Items))
            .order_by(PurchaseModel.Date.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
        
        return [self._to_entity(model) for model in purchases], total_count

    def update(self, purchase: Purchase) -> Purchase:
        """Update purchase."""
        model = self.db.query(PurchaseModel).filter(PurchaseModel.Id == purchase.Id).first()
        if not model:
            return purchase
        self._apply_entity(model, purchase)
        if purchase.Items is not None:
            model.Items.clear()
            model.Items.extend([
                PurchaseItemModel(
                    ProductId=item.ProductId,
                    ProductName=item.ProductName,
                    Quantity=item.Quantity,
                    UnitCost=item.UnitCost,
                    Subtotal=item.Subtotal,
                )
                for item in purchase.Items
            ])
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, purchase_id: int) -> bool:
        """Delete purchase."""
        model = self.db.query(PurchaseModel).filter(PurchaseModel.Id == purchase_id).first()
        if model:
            self.db.delete(model)
            self.db.commit()
            return True
        return False

