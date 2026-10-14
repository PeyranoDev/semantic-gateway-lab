"""
Activity Service for creating audit logs.
"""
from typing import Optional, Dict, Any
import json
from datetime import datetime

from app.domain.entities.activity import Activity, ActivityImportance, ActivityType
from app.domain.ports.activity_repository import ActivityRepositoryPort


class ActivityService:
    """Service for logging user and system activities."""
    
    def __init__(self, activity_repository: ActivityRepositoryPort):
        self.activity_repository = activity_repository

    def log(
        self,
        type: str,
        action: str,
        entity_type: str,
        entity_id: str,
        grocery_id: Optional[int] = None,
        user_id: Optional[str | int] = None,
        importance: str = ActivityImportance.MEDIUM,
        detail: Optional[Dict[str, Any]] = None
    ) -> Activity:
        """
        Log an activity.
        
        Args:
            type: ActivityType (Venta, Compra, etc.)
            action: Human readable description
            entity_type: Technical name of entity (Sale, Product, etc.)
            entity_id: ID of the entity
            grocery_id: Tenant ID
            user_id: ID of user performing action (optional for system actions)
            importance: ActivityImportance (low, medium, high, critical)
            detail: Optional dictionary with extra data (will be JSON encoded)
        """
        detail_json = json.dumps(detail) if detail else None
        
        activity = Activity(
            Id=None,
            Type=type,
            Action=action,
            EntityType=entity_type,
            EntityId=str(entity_id),
            Detail=detail_json,
            Importance=importance,
            CreatedAt=datetime.utcnow(),
            UserId=user_id,
            GroceryId=grocery_id,
            User=None,
        )

        return self.activity_repository.create(activity)
