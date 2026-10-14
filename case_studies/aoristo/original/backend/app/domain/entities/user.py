"""User domain entity."""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.domain.entities.profiles import VerdusoftProfile, RedVecinaProfile


@dataclass
class User:
    Id: Optional[UUID]
    Name: str
    Email: str
    PasswordHash: str
    IsActive: bool
    IsGlobalSuperAdmin: bool = False
    VerdusoftProfile: Optional[VerdusoftProfile] = None
    RedVecinaProfile: Optional[RedVecinaProfile] = None
