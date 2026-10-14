"""Activity repository interface."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ..entities.activity import Activity


class ActivityRepositoryPort(ABC):
    """Abstract interface for activity persistence and queries."""

    @abstractmethod
    def create(self, activity: Activity) -> Activity:
        """Create a new activity."""
        pass

    @abstractmethod
    def get_recent(
        self,
        grocery_id: int,
        since_date: datetime,
        count: int,
        allowed_importances: Optional[List[str]] = None,
    ) -> List[Activity]:
        """Get recent activities for a grocery with optional importance filtering."""
        pass
