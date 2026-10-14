"""
Domain ports for Building and Unit repositories.
"""
from typing import Protocol, Optional, List
from uuid import UUID

from ..entities.redvecina import Building, Unit


class BuildingRepositoryPort(Protocol):
    def create(self, building: Building) -> Building:
        ...

    def get_by_id(self, building_id: UUID) -> Optional[Building]:
        ...

    def get_all(self, is_active: Optional[bool] = None) -> List[Building]:
        ...

    def update(self, building: Building) -> Building:
        ...

    def delete(self, building_id: UUID) -> bool:
        ...


class UnitRepositoryPort(Protocol):
    def create(self, unit: Unit) -> Unit:
        ...

    def get_by_id(self, unit_id: UUID) -> Optional[Unit]:
        ...

    def get_by_building(self, building_id: UUID) -> List[Unit]:
        ...

    def update(self, unit: Unit) -> Unit:
        ...

    def delete(self, unit_id: UUID) -> bool:
        ...
