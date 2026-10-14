"""User profile domain entities."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.domain.entities.grocery import Grocery


@dataclass
class VerdusoftProfile:
    Id: Optional[UUID]
    UserId: Optional[UUID]
    GroceryId: Optional[int]
    Role: Optional[int]
    Grocery: Optional[Grocery] = None


@dataclass
class RedVecinaProfile:
    Id: Optional[UUID]
    UserId: Optional[UUID]
    UnitId: Optional[UUID]
    BuildingId: Optional[UUID]
    Role: Optional[str]
