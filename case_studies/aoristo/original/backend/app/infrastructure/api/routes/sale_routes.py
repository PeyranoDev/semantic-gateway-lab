"""
Sale routes - all operations via Use Cases.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.application.schemas import (
    CreateSaleRequest,
    SaleResponse,
    SaleItemResponse,
    PaginatedSalesResponse,
    ApiResponse,
)
from app.infrastructure.api.dependencies import get_current_user, get_tenant_grocery_id, CurrentUser
from app.infrastructure.api.dependencies.service_guards import require_verdusoft_user
from app.infrastructure.repositories import PostgresSaleRepository, PostgresInventoryRepository, PostgresGroceryRepository
from app.application.use_cases.sale import (
    CreateSaleUseCase,
    GetSalesUseCase,
    GetPaginatedSalesUseCase,
    GetSaleByIdUseCase,
    CreateSaleDTO,
    SaleItemDTO,
    SalesFilterDTO,
    AppliedPromotionDTO,
)
from app.domain.exceptions import InsufficientStockError, SaleNotFoundError
from app.application.services.activity_service import ActivityService
from app.domain.entities.activity import ActivityType, ActivityImportance
from app.infrastructure.repositories.postgres_activity_repository import PostgresActivityRepository

router = APIRouter(prefix="/Sales", tags=["sales"])


def _sale_to_response(sale) -> SaleResponse:
    """Convert domain model to response schema."""
    return SaleResponse(
        id=sale.Id,
        date=sale.Date,
        total=float(sale.Total),
        subtotal=float(sale.Subtotal) if sale.Subtotal else None,
        discount=float(sale.Discount) if sale.Discount else None,
        discountPercent=float(sale.DiscountPercent) if sale.DiscountPercent else None,
        userId=str(sale.UserId),
        name=sale.User.Name if sale.User else None,
        items=[
            SaleItemResponse(
                productId=item.ProductId,
                productName=item.ProductName,
                quantity=float(item.Quantity),
                unitPrice=float(item.UnitPrice),
                subtotal=float(item.Subtotal)
            )
            for item in sale.Items
        ],
        paymentMethod=sale.PaymentMethod,
        status=sale.Status
    )


@router.get("", response_model=ApiResponse[List[SaleResponse]])

def get_sales(
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_verdusoft_user),
    grocery_id: int = Depends(get_tenant_grocery_id)
):
    """Get all sales with optional date filter."""
    repo = PostgresSaleRepository(db)
    use_case = GetSalesUseCase(repo)
    
    filters = SalesFilterDTO(
        start_date=datetime.fromisoformat(startDate) if startDate else None,
        end_date=datetime.fromisoformat(endDate) if endDate else None
    )
    
    sales = use_case.execute(grocery_id, filters)
    return ApiResponse(data=[_sale_to_response(sale) for sale in sales])


@router.get("/paginated", response_model=ApiResponse[PaginatedSalesResponse])

def get_paginated_sales(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_verdusoft_user),
    grocery_id: int = Depends(get_tenant_grocery_id)
):
    """Get paginated sales."""
    repo = PostgresSaleRepository(db)
    use_case = GetPaginatedSalesUseCase(repo)
    
    if status == "all":
        status = None

    filters = SalesFilterDTO(
        start_date=datetime.fromisoformat(startDate) if startDate else None,
        end_date=datetime.fromisoformat(endDate) if endDate else None,
        status=status
    )
    
    result = use_case.execute(grocery_id, page, pageSize, filters)
    
    return ApiResponse(data=PaginatedSalesResponse(
        items=[_sale_to_response(sale) for sale in result.items],
        page=result.page,
        pageSize=result.page_size,
        totalCount=result.total_count,
        totalPages=result.total_pages,
        hasNextPage=result.has_next_page,
        hasPreviousPage=result.has_previous_page
    ))


@router.get("/{sale_id}", response_model=ApiResponse[SaleResponse])

def get_sale_by_id(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_verdusoft_user)
):
    """Get sale by ID."""
    repo = PostgresSaleRepository(db)
    use_case = GetSaleByIdUseCase(repo)
    
    try:
        sale = use_case.execute(sale_id)
    except SaleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    return ApiResponse(data=_sale_to_response(sale))


@router.post("", response_model=ApiResponse[SaleResponse])

def create_sale(
    request: CreateSaleRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_verdusoft_user),
    grocery_id: int = Depends(get_tenant_grocery_id)
):
    """Create a new sale."""
    sale_repo = PostgresSaleRepository(db)
    inv_repo = PostgresInventoryRepository(db)
    # grocery_repo is no longer needed for global tax rate
    
    use_case = CreateSaleUseCase(sale_repo, inv_repo)
    
    try:
        sale = use_case.execute(CreateSaleDTO(
            user_id=current_user.id,
            grocery_id=grocery_id,
            items=[
                SaleItemDTO(
                    product_id=item.productId,
                    product_name=item.productName,
                    quantity=item.quantity,
                    unit_price=item.unitPrice
                )
                for item in request.items
            ],
            payment_method=request.paymentMethod or "efectivo",
            status=request.status or "completed",
            discount=request.discount or 0.0,
            date=request.date,
            applied_promotions=[
                AppliedPromotionDTO(
                    promotion_id=p.promotionId,
                    promotion_name=p.promotionName,
                    type=p.type,
                    discount_amount=p.discountAmount,
                    discount_percent=p.discountPercent
                )
                for p in request.appliedPromotions or []
            ]
        ))
    except InsufficientStockError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
    # Reload with items
    sale = sale_repo.get_by_id(sale.Id)
    
    # Log activity
    ActivityService(PostgresActivityRepository(db)).log(
        type=ActivityType.SALE,
        action=f"Venta #{sale.Id} por ${sale.Total:.2f}",
        entity_type="Sale",
        entity_id=str(sale.Id),
        user_id=current_user.id,
        grocery_id=grocery_id,
        importance=ActivityImportance.MEDIUM,
        detail={"total": float(sale.Total), "items": len(sale.Items)}
    )
    
    return ApiResponse(data=_sale_to_response(sale))


@router.post("/{sale_id}/cancel", response_model=ApiResponse[SaleResponse])

def cancel_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_verdusoft_user)
):
    """
    Cancel a pending sale and restore stock.
    Example: POST /api/Sales/123/cancel
    """
    from app.application.use_cases.sale import CancelSaleUseCase, SaleError 
    
    repo_sale = PostgresSaleRepository(db)
    repo_inv = PostgresInventoryRepository(db)
    use_case = CancelSaleUseCase(repo_sale, repo_inv)
    
    try:
        sale = use_case.execute(sale_id, current_user.id)
    except SaleNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SaleError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        
    # Log activity
    ActivityService(PostgresActivityRepository(db)).log(
        type=ActivityType.SALE,
        action=f"Venta #{sale.Id} cancelada",
        entity_type="Sale",
        entity_id=str(sale.Id),
        user_id=current_user.id,
        grocery_id=current_user.grocery_id,
        importance=ActivityImportance.HIGH
    )
        
    return ApiResponse(data=_sale_to_response(sale))
