import uuid


import enum


from datetime import datetime


from sqlalchemy import Column, String, ForeignKey, Integer, Boolean, Float, DateTime, Text, Enum as SQLEnum


from sqlalchemy.dialects.postgresql import UUID


from sqlalchemy.orm import relationship


from app.domain.models.base import Base


class Building(Base):
    """
    Represents a Consortium or Building.
    Equivalent to 'Grocery' in Verdusoft context (= Tenant).
    """
    __tablename__ = "Buildings"

    Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    Name = Column(String(100), nullable=False)
    Address = Column(String(200), nullable=True)
    Cuit = Column(String(20), nullable=True)
    IsActive = Column(Boolean, default=True)
    
    # Relationships
    Units = relationship("Unit", back_populates="Building", cascade="all, delete-orphan")
    # Admins/Staff might be linked via RedVecinaProfile.BuildingId directly?
    # Yes, typically Profiles link to Building.
    Profiles = relationship("RedVecinaProfile", back_populates="Building")


class Unit(Base):
    """
    Represents a functional unit (Department, House, Garage) within a Building.
    """
    __tablename__ = "Units"

    Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    BuildingId = Column(UUID(as_uuid=True), ForeignKey("Buildings.Id"), nullable=False)
    
    UnitNumber = Column(String(20), nullable=False) # e.g. "4B", "PB-1"
    Floor = Column(String(10), nullable=True)
    
    # Financials (optional for now)
    MonthlyFee = Column(Float, default=0.0)
    Debt = Column(Float, default=0.0)
    
    # Relationships
    Building = relationship("Building", back_populates="Units")
    # Residents live here
    Profiles = relationship("RedVecinaProfile", back_populates="Unit")
    Invitations = relationship("Invitation", back_populates="Unit", cascade="all, delete-orphan")


class Invitation(Base):
    """
    Invitation links for new residents to register.
    """
    __tablename__ = "Invitations"

    Id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    UnitId = Column(UUID(as_uuid=True), ForeignKey("Units.Id"), nullable=False)
    
    Token = Column(String(100), unique=True, nullable=False)
    CurrentUses = Column(Integer, default=0)
    MaxUses = Column(Integer, default=5)
    ExpiresAt = Column(DateTime, nullable=False)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    Unit = relationship("Unit", back_populates="Invitations")


