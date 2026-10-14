"""Grocery domain entity."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Grocery:
    Id: Optional[int]
    Name: str
    Address: Optional[str]
    Phone: Optional[str]
    Email: Optional[str]
    IsActive: bool
    CreatedAt: Optional[datetime]
    UpdatedAt: Optional[datetime]
