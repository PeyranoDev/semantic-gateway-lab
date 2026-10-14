"""Product domain entity."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    Id: Optional[int]
    Name: str
