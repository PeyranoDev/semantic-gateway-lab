"""
Invitation Schemas (DTOs).
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class InvitationBase(BaseModel):
    UnitId: UUID
    MaxUses: int = Field(default=5, ge=1, le=50)
    ValidDays: int = Field(default=7, ge=1, le=30)


class InvitationCreate(InvitationBase):
    pass


class InvitationResponse(BaseModel):
    Id: UUID
    UnitId: UUID
    Token: str
    CurrentUses: int
    MaxUses: int
    ExpiresAt: datetime
    CreatedAt: datetime

    class Config:
        from_attributes = True


class ValidateInvitationRequest(BaseModel):
    Token: str = Field(..., min_length=1)


class ValidateInvitationResponse(BaseModel):
    Id: UUID
    UnitId: UUID
    CurrentUses: int
    MaxUses: int
    ExpiresAt: datetime
    IsValid: bool
    Message: str
