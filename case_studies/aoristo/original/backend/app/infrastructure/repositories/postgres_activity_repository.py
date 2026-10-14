"""PostgreSQL Activity Repository implementation."""
from datetime import datetime, timedelta
from typing import List, Optional, cast
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from ...domain.entities.activity import Activity
from ...domain.entities.user import User
from ...domain.models.activity import Activity as ActivityModel
from ...domain.models.user import User as UserModel
from ...domain.ports.activity_repository import ActivityRepositoryPort


class PostgresActivityRepository(ActivityRepositoryPort):
    """PostgreSQL implementation of ActivityRepositoryPort."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _user_to_entity(model: UserModel | None) -> User | None:
        if not model:
            return None
        return User(
            Id=cast(Optional[UUID], model.Id),
            Name=str(model.Name),
            Email=str(model.Email),
            PasswordHash=str(model.PasswordHash),
            IsActive=bool(model.IsActive),
            IsGlobalSuperAdmin=bool(model.IsGlobalSuperAdmin),
            VerdusoftProfile=None,
            RedVecinaProfile=None,
        )

    def _to_entity(self, model: ActivityModel) -> Activity:
        return Activity(
            Id=cast(Optional[int], model.Id),
            Type=str(model.Type),
            Action=str(model.Action),
            EntityType=str(model.EntityType) if model.EntityType is not None else None,
            EntityId=str(model.EntityId) if model.EntityId is not None else None,
            Detail=str(model.Detail) if model.Detail is not None else None,
            Importance=str(model.Importance),
            CreatedAt=cast(datetime, model.CreatedAt),
            UserId=cast(Optional[UUID], model.UserId),
            GroceryId=cast(Optional[int], model.GroceryId),
            User=self._user_to_entity(getattr(model, "User", None)),
        )

    def create(self, activity: Activity) -> Activity:
        # Avoid duplicate logs created in quick succession for the same entity/action.
        if activity.EntityType and activity.EntityId:
            since = activity.CreatedAt - timedelta(seconds=2)
            existing = (
                self.db.query(ActivityModel)
                .filter(
                    ActivityModel.Type == activity.Type,
                    ActivityModel.Action == activity.Action,
                    ActivityModel.EntityType == activity.EntityType,
                    ActivityModel.EntityId == activity.EntityId,
                    ActivityModel.UserId == activity.UserId,
                    ActivityModel.GroceryId == activity.GroceryId,
                    ActivityModel.CreatedAt >= since,
                )
                .order_by(desc(ActivityModel.CreatedAt))
                .first()
            )
            if existing:
                return self._to_entity(existing)

        model = ActivityModel(
            Type=activity.Type,
            Action=activity.Action,
            EntityType=activity.EntityType,
            EntityId=activity.EntityId,
            Detail=activity.Detail,
            Importance=activity.Importance,
            CreatedAt=activity.CreatedAt,
            UserId=activity.UserId,
            GroceryId=activity.GroceryId,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_recent(
        self,
        grocery_id: int,
        since_date: datetime,
        count: int,
        allowed_importances: Optional[List[str]] = None,
    ) -> List[Activity]:
        query = (
            self.db.query(ActivityModel)
            .options(joinedload(ActivityModel.User))
            .filter(
                ActivityModel.GroceryId == grocery_id,
                ActivityModel.CreatedAt >= since_date,
            )
        )

        if allowed_importances is not None:
            query = query.filter(ActivityModel.Importance.in_(allowed_importances))

        models = query.order_by(desc(ActivityModel.CreatedAt)).limit(count).all()
        return [self._to_entity(model) for model in models]
