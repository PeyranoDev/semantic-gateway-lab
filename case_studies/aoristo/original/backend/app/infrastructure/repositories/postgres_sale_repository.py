"""
PostgreSQL Sale Repository implementation.
"""
from typing import List, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from app.domain.entities.sale import Sale, SaleItem, SalePromotion
from app.domain.entities.user import User
from app.domain.models.sale import Sale as SaleModel
from app.domain.models.sale import SaleItem as SaleItemModel
from app.domain.models.sale import SalePromotion as SalePromotionModel
from app.domain.models.user import User as UserModel
from app.domain.enums.sale_status import SaleStatus
from app.domain.ports.sale_repository import SaleRepositoryPort


class PostgresSaleRepository(SaleRepositoryPort):
    """PostgreSQL implementation of SaleRepositoryPort."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _user_to_entity(model: UserModel | None) -> User | None:
        if not model:
            return None
        return User(
            Id=model.Id,
            Name=model.Name,
            Email=model.Email,
            PasswordHash=model.PasswordHash,
            IsActive=model.IsActive,
            IsGlobalSuperAdmin=model.IsGlobalSuperAdmin,
            VerdusoftProfile=None,
            RedVecinaProfile=None,
        )

    @staticmethod
    def _item_to_entity(model: SaleItemModel) -> SaleItem:
        return SaleItem(
            Id=model.Id,
            SaleId=model.SaleId,
            ProductId=model.ProductId,
            ProductName=model.ProductName,
            Quantity=float(model.Quantity),
            UnitPrice=float(model.UnitPrice),
            Subtotal=float(model.Subtotal),
        )

    @staticmethod
    def _promotion_to_entity(model: SalePromotionModel) -> SalePromotion:
        return SalePromotion(
            Id=model.Id,
            SaleId=model.SaleId,
            PromotionId=model.PromotionId,
            PromotionName=model.PromotionName,
            DiscountAmount=float(model.DiscountAmount),
            DiscountPercent=float(model.DiscountPercent) if model.DiscountPercent is not None else None,
        )

    def _to_entity(self, model: SaleModel) -> Sale:
        return Sale(
            Id=model.Id,
            Date=model.Date,
            Subtotal=float(model.Subtotal),
            Discount=float(model.Discount),
            DiscountPercent=float(model.DiscountPercent) if model.DiscountPercent is not None else None,
            Total=float(model.Total),
            PaymentMethod=model.PaymentMethod,
            Status=model.Status,
            MpPaymentId=model.MpPaymentId,
            UserId=model.UserId,
            GroceryId=model.GroceryId,
            Items=[self._item_to_entity(item) for item in model.Items] if model.Items else [],
            Promotions=[self._promotion_to_entity(promo) for promo in getattr(model, "Promotions", [])] if getattr(model, "Promotions", None) else [],
            User=self._user_to_entity(getattr(model, "User", None)),
            Grocery=None,
        )

    @staticmethod
    def _apply_entity(model: SaleModel, entity: Sale) -> SaleModel:
        model.Date = entity.Date
        model.Subtotal = entity.Subtotal
        model.Discount = entity.Discount
        model.DiscountPercent = entity.DiscountPercent
        model.Total = entity.Total
        model.PaymentMethod = entity.PaymentMethod
        model.Status = entity.Status
        model.MpPaymentId = entity.MpPaymentId
        model.UserId = entity.UserId
        model.GroceryId = entity.GroceryId
        return model

    def create(self, sale: Sale) -> Sale:
        """Create sale with items."""
        model = SaleModel(
            Date=sale.Date,
            Subtotal=sale.Subtotal,
            Discount=sale.Discount,
            DiscountPercent=sale.DiscountPercent,
            Total=sale.Total,
            PaymentMethod=sale.PaymentMethod,
            Status=sale.Status,
            MpPaymentId=sale.MpPaymentId,
            UserId=sale.UserId,
            GroceryId=sale.GroceryId,
        )
        model.Items = [
            SaleItemModel(
                ProductId=item.ProductId,
                ProductName=item.ProductName,
                Quantity=item.Quantity,
                UnitPrice=item.UnitPrice,
                Subtotal=item.Subtotal,
            )
            for item in (sale.Items or [])
        ]
        model.Promotions = [
            SalePromotionModel(
                PromotionId=promo.PromotionId,
                PromotionName=promo.PromotionName,
                DiscountAmount=promo.DiscountAmount,
                DiscountPercent=promo.DiscountPercent,
            )
            for promo in (sale.Promotions or [])
        ]
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, sale_id: int) -> Optional[Sale]:
        """Get sale with items and user."""
        model = (
            self.db.query(SaleModel)
            .options(
                joinedload(SaleModel.Items),
                joinedload(SaleModel.User)
            )
            .filter(SaleModel.Id == sale_id)
            .first()
        )
        return self._to_entity(model) if model else None

    def get_all(
        self,
        grocery_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[Sale]:
        """Get sales with optional date filter."""
        query = (
            self.db.query(SaleModel)
            .options(joinedload(SaleModel.Items), joinedload(SaleModel.User))
            .filter(SaleModel.GroceryId == grocery_id)
        )
        
        if start_date:
            query = query.filter(SaleModel.Date >= start_date)
        if end_date:
            query = query.filter(SaleModel.Date <= end_date)
        if status:
            query = query.filter(SaleModel.Status == status)
        
        return [self._to_entity(model) for model in query.order_by(SaleModel.Date.desc()).all()]

    def get_paginated(
        self,
        grocery_id: int,
        page: int,
        page_size: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> Tuple[List[Sale], int]:
        """Get paginated sales."""
        query = self.db.query(SaleModel).filter(SaleModel.GroceryId == grocery_id)
        
        if start_date:
            query = query.filter(SaleModel.Date >= start_date)
        if end_date:
            query = query.filter(SaleModel.Date <= end_date)
        if status:
            query = query.filter(SaleModel.Status == status)
        
        total_count = query.count()
        
        items = (
            query
            .options(joinedload(SaleModel.Items), joinedload(SaleModel.User))
            .order_by(SaleModel.Date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        return [self._to_entity(model) for model in items], total_count

    def get_today_stats(self, grocery_id: int) -> dict:
        """Get today's sales statistics."""
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        result = (
            self.db.query(
                func.coalesce(func.sum(SaleModel.Total), 0).label("total"),
                func.count(SaleModel.Id).label("count")
            )
            .filter(
                SaleModel.GroceryId == grocery_id,
                SaleModel.Date >= today_start,
                SaleModel.Date <= today_end,
                SaleModel.Status == SaleStatus.COMPLETED.value
            )
            .first()
        )
        
        return {
            "total": float(result.total) if result else 0,
            "count": result.count if result else 0
        }

    def update(self, sale: Sale) -> Sale:
        """Update sale."""
        model = self.db.query(SaleModel).filter(SaleModel.Id == sale.Id).first()
        if not model:
            return sale
        self._apply_entity(model, sale)
        if sale.Items is not None:
            model.Items.clear()
            model.Items.extend([
                SaleItemModel(
                    ProductId=item.ProductId,
                    ProductName=item.ProductName,
                    Quantity=item.Quantity,
                    UnitPrice=item.UnitPrice,
                    Subtotal=item.Subtotal,
                )
                for item in sale.Items
            ])
        if sale.Promotions is not None:
            model.Promotions.clear()
            model.Promotions.extend([
                SalePromotionModel(
                    PromotionId=promo.PromotionId,
                    PromotionName=promo.PromotionName,
                    DiscountAmount=promo.DiscountAmount,
                    DiscountPercent=promo.DiscountPercent,
                )
                for promo in sale.Promotions
            ])
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)
