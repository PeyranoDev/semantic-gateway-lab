"""
PostgreSQL Grocery Repository implementation.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.domain.entities.grocery import Grocery
from app.domain.models.grocery import Grocery as GroceryModel
from app.domain.ports.grocery_repository import GroceryRepositoryPort


class PostgresGroceryRepository(GroceryRepositoryPort):
    """PostgreSQL implementation of GroceryRepositoryPort."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_entity(model: GroceryModel) -> Grocery:
        return Grocery(
            Id=model.Id,
            Name=model.Name,
            Address=model.Address,
            Phone=model.Phone,
            Email=model.Email,
            IsActive=model.IsActive,
            CreatedAt=model.CreatedAt,
            UpdatedAt=model.UpdatedAt,
        )

    @staticmethod
    def _apply_entity(model: GroceryModel, entity: Grocery) -> GroceryModel:
        model.Name = entity.Name
        model.Address = entity.Address
        model.Phone = entity.Phone
        model.Email = entity.Email
        model.IsActive = entity.IsActive
        return model

    def create(self, grocery: Grocery) -> Grocery:
        """Create grocery."""
        model = GroceryModel(
            Name=grocery.Name,
            Address=grocery.Address,
            Phone=grocery.Phone,
            Email=grocery.Email,
            IsActive=grocery.IsActive,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, grocery_id: int) -> Optional[Grocery]:
        """Get grocery by ID."""
        model = self.db.query(GroceryModel).filter(GroceryModel.Id == grocery_id).first()
        return self._to_entity(model) if model else None

    def get_all(self) -> List[Grocery]:
        """Get all groceries."""
        return [
            self._to_entity(model)
            for model in self.db.query(GroceryModel).filter(GroceryModel.IsActive == True).all()
        ]

    def update(self, grocery: Grocery) -> Grocery:
        """Update grocery."""
        model = self.db.query(GroceryModel).filter(GroceryModel.Id == grocery.Id).first()
        if not model:
            return grocery
        self._apply_entity(model, grocery)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, grocery_id: int) -> bool:
        """Soft delete grocery."""
        model = self.db.query(GroceryModel).filter(GroceryModel.Id == grocery_id).first()
        if model:
            model.IsActive = False
            self.db.commit()
            return True
        return False

