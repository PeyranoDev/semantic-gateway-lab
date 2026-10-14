"""
Promotion model — V2.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from typing import Optional

from app.domain.models.base import Base
from app.domain.enums import PromotionType


class Promotion(Base):
    """Promotion/discount entity."""
    __tablename__ = "Promotions"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String(200), nullable=False)
    Description = Column(String(500), nullable=True)
    Type = Column(String(50), nullable=False)

    # ── V2 columns ──
    Rules = Column(JSON, nullable=True)
    Stackable = Column(Boolean, default=False, nullable=False)
    MaxUsesPerTransaction = Column(Integer, nullable=True)
    Priority = Column(Integer, default=0, nullable=False)

    # ── Legacy columns (kept for backward compat) ──
    Value = Column(String(50), nullable=True)
    Condition = Column(JSON, nullable=True)

    StartDate = Column(DateTime, nullable=False)
    EndDate = Column(DateTime, nullable=False)
    Active = Column(Boolean, default=True, nullable=False)

    GroceryId = Column(Integer, ForeignKey("Groceries.Id"), nullable=False)

    CreatedAt = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    UpdatedAt = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    Grocery = relationship("Grocery")

    @property
    def type_enum(self) -> Optional[PromotionType]:
        """Get type as enum."""
        try:
            return PromotionType(self.Type)
        except ValueError:
            return None
