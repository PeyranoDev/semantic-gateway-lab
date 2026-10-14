from dataclasses import dataclass, field


from datetime import datetime


from typing import Optional


from uuid import UUID


@dataclass
class Building:
    """Building/Consortium entity."""
    id: Optional[UUID]
    name: str
    address: str
    cuit: str
    is_active: bool = True


@dataclass
class Unit:
    """Residential unit entity."""
    id: Optional[UUID]
    building_id: UUID
    unit_number: str
    floor: Optional[int] = None
    monthly_fee: float = 0.0
    debt: float = 0.0


@dataclass
class Invitation:
    """Unit invitation link entity."""
    id: Optional[UUID]
    unit_id: UUID
    token: str
    current_uses: int = 0
    max_uses: int = 5
    expires_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


