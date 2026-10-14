"""Category domain entity."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    Id: Optional[int]
    Name: str
    Description: Optional[str]
    GroceryId: int
