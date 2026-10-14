"""
PostgreSQL Building and Unit Repository implementations.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.domain.entities.redvecina import Building, Unit
from app.domain.models.redvecina import Building as BuildingModel, Unit as UnitModel


class PostgresBuildingRepository:
    """PostgreSQL implementation for Building repository."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_entity(model: BuildingModel) -> Building:
        return Building(
            id=model.Id,
            name=model.Name,
            address=model.Address,
            cuit=model.Cuit,
            is_active=model.IsActive,
        )

    def create(self, building: Building) -> Building:
        """Create building."""
        model = BuildingModel(
            Name=building.name,
            Address=building.address,
            Cuit=building.cuit,
            IsActive=building.is_active,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, building_id: UUID) -> Optional[Building]:
        """Get building by ID."""
        model = self.db.query(BuildingModel).filter(BuildingModel.Id == building_id).first()
        return self._to_entity(model) if model else None

    def get_all(self, is_active: Optional[bool] = None) -> List[Building]:
        """Get all buildings, optionally filtered by active status."""
        query = self.db.query(BuildingModel)
        if is_active is not None:
            query = query.filter(BuildingModel.IsActive == is_active)
        return [self._to_entity(model) for model in query.all()]

    def update(self, building: Building) -> Building:
        """Update building."""
        model = self.db.query(BuildingModel).filter(BuildingModel.Id == building.id).first()
        if not model:
            raise ValueError(f"Building with id {building.id} not found")
        
        model.Name = building.name
        model.Address = building.address
        model.Cuit = building.cuit
        model.IsActive = building.is_active
        
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, building_id: UUID) -> bool:
        """Delete building."""
        model = self.db.query(BuildingModel).filter(BuildingModel.Id == building_id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True


class PostgresUnitRepository:
    """PostgreSQL implementation for Unit repository."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_entity(model: UnitModel) -> Unit:
        return Unit(
            id=model.Id,
            building_id=model.BuildingId,
            unit_number=model.UnitNumber,
            floor=model.Floor,
            monthly_fee=model.MonthlyFee,
            debt=model.Debt,
        )

    def create(self, unit: Unit) -> Unit:
        """Create unit."""
        model = UnitModel(
            BuildingId=unit.building_id,
            UnitNumber=unit.unit_number,
            Floor=unit.floor,
            MonthlyFee=unit.monthly_fee,
            Debt=unit.debt,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, unit_id: UUID) -> Optional[Unit]:
        """Get unit by ID."""
        model = self.db.query(UnitModel).filter(UnitModel.Id == unit_id).first()
        return self._to_entity(model) if model else None

    def get_by_building(self, building_id: UUID) -> List[Unit]:
        """Get all units for a building."""
        models = self.db.query(UnitModel).filter(UnitModel.BuildingId == building_id).all()
        return [self._to_entity(model) for model in models]

    def update(self, unit: Unit) -> Unit:
        """Update unit."""
        model = self.db.query(UnitModel).filter(UnitModel.Id == unit.id).first()
        if not model:
            raise ValueError(f"Unit with id {unit.id} not found")
        
        model.BuildingId = unit.building_id
        model.UnitNumber = unit.unit_number
        model.Floor = unit.floor
        model.MonthlyFee = unit.monthly_fee
        model.Debt = unit.debt
        
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, unit_id: UUID) -> bool:
        """Delete unit."""
        model = self.db.query(UnitModel).filter(UnitModel.Id == unit_id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True
