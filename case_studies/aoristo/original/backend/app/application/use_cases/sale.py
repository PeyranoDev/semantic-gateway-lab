"""
Sale Use Cases.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime
from decimal import Decimal

from app.domain.entities.sale import Sale, SaleItem, SalePromotion
from app.domain.ports.sale_repository import SaleRepositoryPort
from app.domain.ports.inventory_repository import InventoryRepositoryPort


class SaleError(Exception):
    """Base sale error."""
    pass


class InsufficientStockError(SaleError):
    """Not enough stock for sale."""
    pass


class SaleNotFoundError(SaleError):
    """Sale not found."""
    pass


@dataclass
class SaleItemDTO:
    """Individual sale item data."""
    product_id: int
    product_name: str
    quantity: float
    unit_price: float


@dataclass
class AppliedPromotionDTO:
    promotion_id: str
    promotion_name: str
    type: str
    discount_amount: float
    discount_percent: Optional[float] = None
    promotion_type: Optional[str] = None


@dataclass
class CreateSaleDTO:
    """Data for creating a sale."""
    user_id: str
    grocery_id: int
    items: List[SaleItemDTO]
    payment_method: str = "efectivo"
    discount: float = 0
    discount_percent: Optional[float] = None
    status: str = "completed"
    date: Optional[datetime] = None
    applied_promotions: List[AppliedPromotionDTO] = field(default_factory=list)


@dataclass
class SalesFilterDTO:
    """Filters for sales queries."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


@dataclass
class PaginatedResultDTO:
    """Generic paginated result."""
    items: List
    page: int
    page_size: int
    total_count: int
    total_pages: int
    has_next_page: bool
    has_previous_page: bool


class CreateSaleUseCase:
    """
    Use Case: Create a new sale.
    Validates stock and updates inventory.
    """

    def __init__(
        self,
        sale_repository: SaleRepositoryPort,
        inventory_repository: InventoryRepositoryPort
    ):
        self.sale_repository = sale_repository
        self.inventory_repository = inventory_repository

    def execute(self, dto: CreateSaleDTO) -> Sale:
        """
        Create a sale with items.
        
        1. Validate stock availability
        2. Calculate totals
        3. Create sale record
        4. Deduct from inventory
        
        Raises:
            InsufficientStockError: If not enough stock
        """
        # Build sale items and calculate totals
        sale_items = []
        subtotal = Decimal(0)
        
        for item_dto in dto.items:
            # Validate stock
            inv_item = self.inventory_repository.get_by_product_id(
                item_dto.product_id, dto.grocery_id
            )
            
            if not inv_item or inv_item.Stock < item_dto.quantity:
                available = inv_item.Stock if inv_item else 0
                raise InsufficientStockError(
                    f"Stock insuficiente para {item_dto.product_name}. "
                    f"Disponible: {available}, Solicitado: {item_dto.quantity}"
                )
            
            item_subtotal = Decimal(str(item_dto.quantity)) * Decimal(str(item_dto.unit_price))
            
            subtotal += item_subtotal
            
            sale_items.append(SaleItem(
                Id=None,
                SaleId=None,
                ProductId=item_dto.product_id,
                ProductName=item_dto.product_name,
                Quantity=item_dto.quantity,
                UnitPrice=item_dto.unit_price,
                Subtotal=float(item_subtotal),
            ))
        
        # Apply discount
        discount_amount = Decimal(str(dto.discount))
        if dto.discount_percent:
            discount_amount = subtotal * (Decimal(str(dto.discount_percent)) / 100)
            
        # Add promotions discount
        promotions_discount = Decimal(0)
        sale_promotions = []
        
        for promo in dto.applied_promotions:
            discount = Decimal(str(promo.discount_amount))
            promotions_discount += discount
            
            sale_promotions.append(SalePromotion(
                Id=None,
                SaleId=None,
                PromotionId=int(promo.promotion_id) if promo.promotion_id.isdigit() else None,
                PromotionName=promo.promotion_name,
                DiscountAmount=float(discount),
                DiscountPercent=float(promo.discount_percent) if promo.discount_percent else None,
                PromotionType=promo.promotion_type or promo.type,
            ))
            
        discount_amount += promotions_discount
            
        # Ensure total never goes negative due to stacked discounts
        total = max(Decimal(0), subtotal - discount_amount)
        
        # Create sale
        sale = Sale(
            Id=None,
            Date=dto.date if dto.date else datetime.utcnow(),
            Subtotal=float(subtotal),
            Discount=float(discount_amount),
            DiscountPercent=float(dto.discount_percent) if dto.discount_percent else None,
            Total=float(total),
            PaymentMethod=dto.payment_method,
            Status=dto.status,
            MpPaymentId=None,
            UserId=dto.user_id,
            GroceryId=dto.grocery_id,
            Items=sale_items,
            Promotions=sale_promotions,
            User=None,
            Grocery=None,
        )
        
        created_sale = self.sale_repository.create(sale)
        
        for item_dto in dto.items:
            inv_item = self.inventory_repository.get_by_product_id(
                item_dto.product_id, dto.grocery_id
            )
            if inv_item:
                inv_item.Stock = int(inv_item.Stock - item_dto.quantity)
                inv_item.SalePrice = item_dto.unit_price
                self.inventory_repository.update(inv_item)
        
        return created_sale


class GetSalesUseCase:
    """
    Use Case: Get sales list with optional date filter.
    """

    def __init__(self, sale_repository: SaleRepositoryPort):
        self.sale_repository = sale_repository

    def execute(
        self, 
        grocery_id: int, 
        filters: Optional[SalesFilterDTO] = None
    ) -> List[Sale]:
        """Get all sales for grocery with optional filters."""
        start_date = filters.start_date if filters else None
        end_date = filters.end_date if filters else None
        
        return self.sale_repository.get_all(grocery_id, start_date, end_date)


class GetPaginatedSalesUseCase:
    """
    Use Case: Get paginated sales.
    """

    def __init__(self, sale_repository: SaleRepositoryPort):
        self.sale_repository = sale_repository

    def execute(
        self,
        grocery_id: int,
        page: int,
        page_size: int,
        filters: Optional[SalesFilterDTO] = None
    ) -> PaginatedResultDTO:
        """Get paginated sales."""
        start_date = filters.start_date if filters else None
        end_date = filters.end_date if filters else None
        status = filters.status if filters else None
        
        items, total_count = self.sale_repository.get_paginated(
            grocery_id, page, page_size, start_date, end_date, status
        )
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return PaginatedResultDTO(
            items=items,
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
            has_next_page=page < total_pages,
            has_previous_page=page > 1
        )


class GetSaleByIdUseCase:
    """
    Use Case: Get a single sale by ID.
    """

    def __init__(self, sale_repository: SaleRepositoryPort):
        self.sale_repository = sale_repository

    def execute(self, sale_id: int) -> Sale:
        """
        Get sale by ID.
        
        Raises:
            SaleNotFoundError: If sale not found
        """
        sale = self.sale_repository.get_by_id(sale_id)
        if not sale:
            raise SaleNotFoundError(f"Venta {sale_id} no encontrada.")
        return sale


class CancelSaleUseCase:
    """
    Use Case: Cancel a sale and restore stock.
    Only allows cancelling pending sales.
    """

    def __init__(
        self,
        sale_repository: SaleRepositoryPort,
        inventory_repository: InventoryRepositoryPort
    ):
        self.sale_repository = sale_repository
        self.inventory_repository = inventory_repository

    def execute(self, sale_id: int, user_id: str) -> Sale:
        """
        Cancel sale and restore stock.
        """
        sale = self.sale_repository.get_by_id(sale_id)
        if not sale:
            raise SaleNotFoundError(f"Venta {sale_id} no encontrada.")
            
        if sale.Status != "pending":

             if sale.Status == "completed":
                 raise SaleError("Solo se pueden cancelar ventas pendientes.")
             pass

        sale.Status = "cancelled"
        self.sale_repository.update(sale)
        
        for item in sale.Items:
            inv_item = self.inventory_repository.get_by_product_id(
                item.ProductId, sale.GroceryId
            )
            if inv_item:
                new_stock = int(inv_item.Stock + item.Quantity)
                self.inventory_repository.adjust_stock(inv_item.Id, new_stock)
                
        return sale
