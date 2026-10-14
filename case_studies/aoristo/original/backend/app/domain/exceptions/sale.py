"""
Sale exceptions.
"""
from app.domain.exceptions.base import DomainException


class SaleException(DomainException):
    """Base sale exception."""
    pass


class SaleNotFoundError(SaleException):
    """Sale not found."""
    
    def __init__(self, sale_id: int | None = None):
        message = f"Venta {sale_id} no encontrada." if sale_id else "Venta no encontrada."
        super().__init__(message, "SALE_NOT_FOUND")
