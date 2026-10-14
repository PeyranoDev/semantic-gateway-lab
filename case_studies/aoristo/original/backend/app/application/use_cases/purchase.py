"""
Purchase Use Cases.
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

from app.domain.entities.purchase import Purchase, PurchaseItem
from app.domain.ports.purchase_repository import PurchaseRepositoryPort
from app.domain.ports.inventory_repository import InventoryRepositoryPort
from app.domain.exceptions.base import DomainException
from app.domain.enums import PurchaseStatus


class PurchaseNotFoundError(DomainException):
    """Purchase not found."""
    def __init__(self, purchase_id: int | None = None):
        message = f"Compra {purchase_id} no encontrada." if purchase_id else "Compra no encontrada."
        super().__init__(message, "PURCHASE_NOT_FOUND")


@dataclass
class PurchaseItemDTO:
    """Purchase item data."""
    product_id: Optional[int] = None  # None if new product
    product_name: str = ""
    category_id: int = 0
    quantity: float = 0
    unit_cost: float = 0


@dataclass
class CreatePurchaseDTO:
    """Data for creating purchase."""
    grocery_id: int
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    items: List[PurchaseItemDTO] = None
    notes: Optional[str] = None


@dataclass 
class PurchaseFilterDTO:
    """Filters for purchases."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class GetAllPurchasesUseCase:
    """Get all purchases for a grocery."""
    
    def __init__(self, purchase_repository: PurchaseRepositoryPort):
        self.purchase_repository = purchase_repository
    
    def execute(self, grocery_id: int, filters: Optional[PurchaseFilterDTO] = None) -> List[Purchase]:
        return self.purchase_repository.get_all(
            grocery_id,
            start_date=filters.start_date if filters else None,
            end_date=filters.end_date if filters else None
        )


class GetPaginatedPurchasesUseCase:
    """Get paginated purchases."""
    
    def __init__(self, purchase_repository: PurchaseRepositoryPort):
        self.purchase_repository = purchase_repository
        
    def execute(
        self, 
        grocery_id: int, 
        page: int, 
        page_size: int, 
        filters: Optional[PurchaseFilterDTO] = None
    ) -> "tuple[List[Purchase], int, int, int, int, bool, bool]":
        from dataclasses import dataclass
        
        # Determine filters
        start_date = filters.start_date if filters else None
        end_date = filters.end_date if filters else None
        
        # Get data from repo
        items, total_count = self.purchase_repository.get_paginated(
            grocery_id, page, page_size, start_date, end_date
        )
        
        # Calculate pagination metadata
        import math
        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 0
        has_next_page = page < total_pages
        has_previous_page = page > 1
        
        # Using a simple object/struct to return results, similar to sales
        @dataclass
        class PaginationResult:
            items: List[Purchase]
            page: int
            page_size: int
            total_count: int
            total_pages: int
            has_next_page: bool
            has_previous_page: bool
            
        return PaginationResult(
            items=items,
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
            has_next_page=has_next_page,
            has_previous_page=has_previous_page
        )


class GetPurchaseByIdUseCase:
    """Get purchase by ID."""
    
    def __init__(self, purchase_repository: PurchaseRepositoryPort):
        self.purchase_repository = purchase_repository
    
    def execute(self, purchase_id: int) -> Purchase:
        purchase = self.purchase_repository.get_by_id(purchase_id)
        if not purchase:
            raise PurchaseNotFoundError(purchase_id)
        return purchase


class CreatePurchaseUseCase:
    """Create purchase and update inventory."""
    
    def __init__(
        self, 
        purchase_repository: PurchaseRepositoryPort,
        inventory_repository: InventoryRepositoryPort,
        product_repository=None  # ProductRepositoryPort
    ):
        self.purchase_repository = purchase_repository
        self.inventory_repository = inventory_repository
        self.product_repository = product_repository
    
    def execute(self, dto: CreatePurchaseDTO) -> Purchase:
        from app.domain.entities.product import Product
        from app.domain.entities.inventory import InventoryItem
        from sqlalchemy.exc import IntegrityError
        
        # Calculate totals
        items = []
        total = 0
        
        for item_dto in (dto.items or []):
            # Auto-create Product if new
            product_id = item_dto.product_id
            if not product_id and self.product_repository:
                # Check if product with this name already exists
                existing_product = self.product_repository.get_by_name(item_dto.product_name)
                if existing_product:
                    product_id = existing_product.Id
                else:
                    # Create new global product
                    try:
                        new_product = Product(Id=None, Name=item_dto.product_name)
                        created_product = self.product_repository.create(new_product)
                        product_id = created_product.Id
                    except IntegrityError:
                        # Handle race condition: product was created between check and insert
                        existing_product = self.product_repository.get_by_name(item_dto.product_name)
                        if existing_product:
                            product_id = existing_product.Id
                        else:
                            raise
            
            if not product_id:
                raise ValueError(f"Product ID required for item: {item_dto.product_name}")
            
            subtotal = item_dto.quantity * item_dto.unit_cost
            total += subtotal
            
            items.append(PurchaseItem(
                Id=None,
                PurchaseId=None,
                ProductId=product_id,
                ProductName=item_dto.product_name,
                Quantity=item_dto.quantity,
                UnitCost=item_dto.unit_cost,
                Subtotal=subtotal,
            ))
        
        purchase = Purchase(
            Id=None,
            Date=datetime.utcnow(),
            SupplierId=dto.supplier_id,
            SupplierName=dto.supplier_name,
            Total=total,
            Status=PurchaseStatus.RECEIVED.value,
            Notes=dto.notes,
            GroceryId=dto.grocery_id,
            Items=items,
        )
        
        # Create purchase
        created = self.purchase_repository.create(purchase)
        
        # Update inventory stock or create InventoryItem
        for item_dto in (dto.items or []):
            product_id = item_dto.product_id
            if not product_id:
                # Get the product_id we created/found earlier
                existing_product = self.product_repository.get_by_name(item_dto.product_name)
                product_id = existing_product.Id if existing_product else None
            
            if not product_id:
                continue
            
            inv_item = self.inventory_repository.get_by_product_id(
                product_id, dto.grocery_id
            )
            if inv_item:
                # Update existing inventory
                new_stock = inv_item.Stock + int(item_dto.quantity)
                
                # Update Category if provided/changed
                if item_dto.category_id and item_dto.category_id != inv_item.CategoryId:
                    inv_item.CategoryId = item_dto.category_id
                
                # Update LastPurchasePrice
                inv_item.LastPurchasePrice = item_dto.unit_cost
                
                # Optional: Update Sale Price if it looks like a new batch/update 
                # (For now we only update stock and category, but could update price too)
                if item_dto.unit_cost > inv_item.SalePrice:
                     # If cost is higher than current sale price, we might want to alert or auto-update?
                     # Ignoring price auto-update for safety, but ensuring persistence of other fields.
                     pass
                
                # Persist changes (Category + Stock)
                # adjust_stock might only do SQL UPDATE stock, so we use general update or ensure session commit happens
                inv_item.Stock = new_stock
                # self.inventory_repository.update(inv_item) # If update method exists
                # Or since we are in a session, just modifying the object and committing (which repository methods usually do)
                # But let's check repo methods. adjust_stock is specific.
                # Use update method if available to be clean.
                self.inventory_repository.update(inv_item)
            else:
                # Create new InventoryItem for this grocery
                new_inv_item = InventoryItem(
                    Id=None,
                    ProductId=product_id,
                    GroceryId=dto.grocery_id,
                    CategoryId=item_dto.category_id,
                    Stock=int(item_dto.quantity),
                    SalePrice=item_dto.unit_cost,  # Default sale price = cost
                    LastPurchasePrice=item_dto.unit_cost,
                    Unit="u",
                    MinStock=None,
                    MaxStock=None,
                    LastUpdated=None,
                    Product=None,
                    Category=None,
                    Grocery=None,
                )
                self.inventory_repository.create(new_inv_item)
        
        return created


@dataclass
class UpdatePurchaseDTO:
    """Data for updating purchase."""
    purchase_id: int
    grocery_id: int
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    items: List[PurchaseItemDTO] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class UpdatePurchaseUseCase:
    """Update an existing purchase."""
    
    def __init__(
        self, 
        purchase_repository: PurchaseRepositoryPort,
        inventory_repository: InventoryRepositoryPort,
        product_repository=None
    ):
        self.purchase_repository = purchase_repository
        self.inventory_repository = inventory_repository
        self.product_repository = product_repository
    
    def execute(self, dto: UpdatePurchaseDTO) -> Purchase:
        from app.domain.entities.product import Product
        from app.domain.entities.inventory import InventoryItem
        from sqlalchemy.exc import IntegrityError
        
        # Get existing purchase
        purchase = self.purchase_repository.get_by_id(dto.purchase_id)
        if not purchase:
            raise PurchaseNotFoundError(dto.purchase_id)
        
        # Store old items for inventory adjustment
        old_items = {item.ProductId: item.Quantity for item in purchase.Items}
        
        # Update basic fields
        if dto.supplier_id is not None:
            purchase.SupplierId = dto.supplier_id
        if dto.supplier_name is not None:
            purchase.SupplierName = dto.supplier_name
        if dto.notes is not None:
            purchase.Notes = dto.notes
        if dto.status is not None:
            purchase.Status = dto.status
        
        # Update items if provided
        if dto.items is not None:
            # Clear existing items
            purchase.Items.clear()
            
            new_items = []
            total = 0
            
            for item_dto in dto.items:
                # Auto-create Product if new
                product_id = item_dto.product_id
                if not product_id and self.product_repository:
                    existing_product = self.product_repository.get_by_name(item_dto.product_name)
                    if existing_product:
                        product_id = existing_product.Id
                    else:
                        try:
                            new_product = Product(Id=None, Name=item_dto.product_name)
                            created_product = self.product_repository.create(new_product)
                            product_id = created_product.Id
                        except IntegrityError:
                            existing_product = self.product_repository.get_by_name(item_dto.product_name)
                            if existing_product:
                                product_id = existing_product.Id
                            else:
                                raise
                
                if not product_id:
                    raise ValueError(f"Product ID required for item: {item_dto.product_name}")
                
                subtotal = item_dto.quantity * item_dto.unit_cost
                total += subtotal
                
                new_items.append(PurchaseItem(
                    Id=None,
                    PurchaseId=purchase.Id,
                    ProductId=product_id,
                    ProductName=item_dto.product_name,
                    Quantity=item_dto.quantity,
                    UnitCost=item_dto.unit_cost,
                    Subtotal=subtotal,
                ))
            
            purchase.Items = new_items
            purchase.Total = total
            
            # Adjust inventory: reverse old items, add new items
            for product_id, old_qty in old_items.items():
                inv_item = self.inventory_repository.get_by_product_id(product_id, dto.grocery_id)
                if inv_item:
                    # Subtract old quantity
                    new_stock = max(0, inv_item.Stock - int(old_qty))
                    self.inventory_repository.adjust_stock(inv_item.Id, new_stock)
            
            # Add new quantities
            for item_dto in dto.items:
                product_id = item_dto.product_id
                if not product_id:
                    existing_product = self.product_repository.get_by_name(item_dto.product_name)
                    product_id = existing_product.Id if existing_product else None
                
                if not product_id:
                    continue
                
                inv_item = self.inventory_repository.get_by_product_id(product_id, dto.grocery_id)
                if inv_item:
                    new_stock = inv_item.Stock + int(item_dto.quantity)
                    self.inventory_repository.adjust_stock(inv_item.Id, new_stock)
                else:
                    new_inv_item = InventoryItem(
                        Id=None,
                        ProductId=product_id,
                        GroceryId=dto.grocery_id,
                        CategoryId=item_dto.category_id,
                        Stock=int(item_dto.quantity),
                        SalePrice=item_dto.unit_cost,
                        LastPurchasePrice=None,
                        Unit="u",
                        MinStock=None,
                        MaxStock=None,
                        LastUpdated=None,
                        Product=None,
                        Category=None,
                        Grocery=None,
                    )
                    self.inventory_repository.create(new_inv_item)
        
        return self.purchase_repository.update(purchase)

