"""
Inventory exceptions.
"""
from app.domain.exceptions.base import DomainException


class InventoryException(DomainException):
    """Base inventory exception."""
    pass


class InventoryItemNotFoundError(InventoryException):
    """Inventory item not found."""
    
    def __init__(self, item_id: int | None = None):
        message = f"Item de inventario {item_id} no encontrado." if item_id else "Item no encontrado."
        super().__init__(message, "INVENTORY_ITEM_NOT_FOUND")


class ProductNotFoundError(InventoryException):
    """Product not found."""
    
    def __init__(self, product_id: int | None = None):
        message = f"Producto {product_id} no encontrado." if product_id else "Producto no encontrado."
        super().__init__(message, "PRODUCT_NOT_FOUND")


class InsufficientStockError(InventoryException):
    """Not enough stock for operation."""
    
    def __init__(self, product_name: str, available: int, requested: float):
        message = f"Stock insuficiente para {product_name}. Disponible: {available}, Solicitado: {requested}"
        super().__init__(message, "INSUFFICIENT_STOCK")


class InventoryItemAlreadyExistsError(InventoryException):
    """Inventory item already exists."""
    
    def __init__(self, product_name: str | None = None):
        message = f"El producto {product_name} ya existe en el inventario." if product_name else "El producto ya existe en el inventario."
        super().__init__(message, "INVENTORY_ITEM_ALREADY_EXISTS")
