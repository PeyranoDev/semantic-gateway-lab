"""
Purchase routes - all operations via Use Cases.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.application.schemas.purchase import (
    PurchaseResponse,
    PurchaseItemResponse,
    PaginatedPurchasesResponse,
    CreatePurchaseRequest,
    UpdatePurchaseRequest,
)
from app.application.schemas import ApiResponse
from app.infrastructure.api.dependencies import get_current_user, get_tenant_grocery_id, CurrentUser
from app.infrastructure.api.dependencies.service_guards import require_verdusoft_user
from app.infrastructure.repositories import PostgresPurchaseRepository, PostgresInventoryRepository, PostgresProductRepository
from app.application.use_cases.purchase import (
    GetAllPurchasesUseCase,
    GetPaginatedPurchasesUseCase,
    GetPurchaseByIdUseCase,
    CreatePurchaseUseCase,
    UpdatePurchaseUseCase,
    PurchaseFilterDTO,
    CreatePurchaseDTO,
    UpdatePurchaseDTO,
    PurchaseItemDTO,
    PurchaseNotFoundError,
)
from app.application.services.activity_service import ActivityService
from app.domain.entities.activity import ActivityType, ActivityImportance
from app.infrastructure.repositories.postgres_activity_repository import PostgresActivityRepository

router = APIRouter(prefix="/Purchases", tags=["purchases"])


def _purchase_to_response(purchase) -> PurchaseResponse:
    """Convert domain model to response schema."""
    return PurchaseResponse(
        id=purchase.Id,
        date=purchase.Date,
        supplierId=purchase.SupplierId,
        supplierName=purchase.SupplierName,
        total=float(purchase.Total),
        status=purchase.Status,
        notes=purchase.Notes,
        items=[
            PurchaseItemResponse(
                productId=item.ProductId,
                productName=item.ProductName,
                quantity=float(item.Quantity),
                unitCost=float(item.UnitCost),
                subtotal=float(item.Subtotal)
            )
            for item in purchase.Items
        ]
    )


@router.get("", response_model=ApiResponse[PaginatedPurchasesResponse])

def get_purchases(
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_verdusoft_user),
    grocery_id: int = Depends(get_tenant_grocery_id)
):
    """Get all purchases with optional date filter."""
    repo = PostgresPurchaseRepository(db)
    use_case = GetPaginatedPurchasesUseCase(repo)
    
    start_dt = datetime.fromisoformat(startDate) if startDate else None
    end_dt = datetime.fromisoformat(endDate) if endDate else None
    
    if end_dt:
        # Set to end of day to be inclusive
        end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    filters = PurchaseFilterDTO(
        start_date=start_dt,
        end_date=end_dt
    )
    
    result = use_case.execute(grocery_id, page, pageSize, filters)
    
    return ApiResponse(data=PaginatedPurchasesResponse(
        items=[_purchase_to_response(p) for p in result.items],
        page=result.page,
        pageSize=result.page_size,
        totalCount=result.total_count,
        totalPages=result.total_pages,
        hasNextPage=result.has_next_page,
        hasPreviousPage=result.has_previous_page
    ))


@router.get("/{purchase_id}", response_model=ApiResponse[PurchaseResponse])

def get_purchase_by_id(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_verdusoft_user)
):
    """Get purchase by ID."""
    repo = PostgresPurchaseRepository(db)
    use_case = GetPurchaseByIdUseCase(repo)
    
    try:
        purchase = use_case.execute(purchase_id)
    except PurchaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    return ApiResponse(data=_purchase_to_response(purchase))


@router.post("", response_model=ApiResponse[PurchaseResponse])

def create_purchase(
    request: CreatePurchaseRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_verdusoft_user),
    grocery_id: int = Depends(get_tenant_grocery_id)
):
    """Create a new purchase (restock)."""
    purchase_repo = PostgresPurchaseRepository(db)
    inv_repo = PostgresInventoryRepository(db)
    product_repo = PostgresProductRepository(db)
    use_case = CreatePurchaseUseCase(purchase_repo, inv_repo, product_repo)
    
    purchase = use_case.execute(CreatePurchaseDTO(
        grocery_id=grocery_id,
        supplier_id=request.supplierId,
        supplier_name=request.supplierName,
        notes=request.notes,
        items=[
            PurchaseItemDTO(
                product_id=item.productId,
                product_name=item.productName,
                category_id=item.categoryId,
                quantity=item.quantity,
                unit_cost=item.unitCost
            )
            for item in request.items
        ]
    ))
    
    # Reload with items
    purchase = purchase_repo.get_by_id(purchase.Id)
    
    # Log activity
    ActivityService(PostgresActivityRepository(db)).log(
        type=ActivityType.PURCHASE,
        action=f"Compra #{purchase.Id} a {purchase.SupplierName or 'Proveedor'}",
        entity_type="Purchase",
        entity_id=str(purchase.Id),
        user_id=current_user.id,
        grocery_id=grocery_id,
        importance=ActivityImportance.MEDIUM,
        detail={"total": float(purchase.Total), "items": len(purchase.Items)}
    )
    
    return ApiResponse(data=_purchase_to_response(purchase))


@router.put("/{purchase_id}", response_model=ApiResponse[PurchaseResponse])

def update_purchase(
    purchase_id: int,
    request: UpdatePurchaseRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_verdusoft_user),
    grocery_id: int = Depends(get_tenant_grocery_id)
):
    """Update an existing purchase."""
    purchase_repo = PostgresPurchaseRepository(db)
    inv_repo = PostgresInventoryRepository(db)
    product_repo = PostgresProductRepository(db)
    use_case = UpdatePurchaseUseCase(purchase_repo, inv_repo, product_repo)
    
    try:
        purchase = use_case.execute(UpdatePurchaseDTO(
            purchase_id=purchase_id,
            grocery_id=grocery_id,
            supplier_id=request.supplierId,
            supplier_name=request.supplierName,
            notes=request.notes,
            status=request.status,
            items=[
                PurchaseItemDTO(
                    product_id=item.productId,
                    product_name=item.productName,
                    category_id=item.categoryId,
                    quantity=item.quantity,
                    unit_cost=item.unitCost
                )
                for item in request.items
            ] if request.items else None
        ))
    except PurchaseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    # Reload with items
    purchase = purchase_repo.get_by_id(purchase.Id)
    
    # Log activity
    ActivityService(PostgresActivityRepository(db)).log(
        type=ActivityType.PURCHASE,
        action=f"Compra #{purchase.Id} actualizada",
        entity_type="Purchase",
        entity_id=str(purchase.Id),
        user_id=current_user.id,
        grocery_id=grocery_id,
        importance=ActivityImportance.MEDIUM,
        detail={"total": float(purchase.Total), "items": len(purchase.Items)}
    )
    
    return ApiResponse(data=_purchase_to_response(purchase))
