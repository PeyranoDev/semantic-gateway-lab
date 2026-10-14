"""
Category exceptions.
"""
from app.domain.exceptions.base import DomainException


class CategoryException(DomainException):
    """Base category exception."""
    pass


class CategoryNotFoundError(CategoryException):
    """Category not found."""
    
    def __init__(self, category_id: int | None = None):
        message = f"Categoría {category_id} no encontrada." if category_id else "Categoría no encontrada."
        super().__init__(message, "CATEGORY_NOT_FOUND")
