"""
PostgreSQL User Repository implementation.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.domain.entities.user import User
from app.domain.entities.profiles import VerdusoftProfile, RedVecinaProfile
from app.domain.entities.grocery import Grocery
from app.domain.models.user import User as UserModel
from app.domain.models.profiles import VerdusoftProfile as VerdusoftProfileModel
from app.domain.models.profiles import RedVecinaProfile as RedVecinaProfileModel
from app.domain.models.grocery import Grocery as GroceryModel
from app.domain.ports.user_repository import UserRepositoryPort


class PostgresUserRepository(UserRepositoryPort):
    """PostgreSQL implementation of UserRepositoryPort."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _grocery_to_entity(model: GroceryModel | None) -> Grocery | None:
        if not model:
            return None
        return Grocery(
            Id=model.Id,
            Name=model.Name,
            Address=model.Address,
            Phone=model.Phone,
            Email=model.Email,
            IsActive=model.IsActive,
            CreatedAt=model.CreatedAt,
            UpdatedAt=model.UpdatedAt,
        )

    def _verdusoft_profile_to_entity(self, model: VerdusoftProfileModel | None) -> VerdusoftProfile | None:
        if not model:
            return None
        return VerdusoftProfile(
            Id=model.Id,
            UserId=model.UserId,
            GroceryId=model.GroceryId,
            Role=model.Role,
            Grocery=self._grocery_to_entity(model.Grocery),
        )

    @staticmethod
    def _redvecina_profile_to_entity(model: RedVecinaProfileModel | None) -> RedVecinaProfile | None:
        if not model:
            return None
        return RedVecinaProfile(
            Id=model.Id,
            UserId=model.UserId,
            UnitId=model.UnitId,
            BuildingId=model.BuildingId,
            Role=model.Role,
        )

    def _to_entity(self, model: UserModel) -> User:
        return User(
            Id=model.Id,
            Name=model.Name,
            Email=model.Email,
            PasswordHash=model.PasswordHash,
            IsActive=model.IsActive,
            IsGlobalSuperAdmin=model.IsGlobalSuperAdmin,
            VerdusoftProfile=self._verdusoft_profile_to_entity(model.VerdusoftProfile),
            RedVecinaProfile=self._redvecina_profile_to_entity(model.RedVecinaProfile),
        )

    @staticmethod
    def _apply_entity(model: UserModel, entity: User) -> UserModel:
        model.Name = entity.Name
        model.Email = entity.Email
        model.PasswordHash = entity.PasswordHash
        model.IsActive = entity.IsActive
        model.IsGlobalSuperAdmin = entity.IsGlobalSuperAdmin
        return model

    def create(self, user: User) -> User:
        """Create a new user."""
        model = UserModel(
            Name=user.Name,
            Email=user.Email,
            PasswordHash=user.PasswordHash,
            IsActive=user.IsActive,
            IsGlobalSuperAdmin=user.IsGlobalSuperAdmin,
        )

        if user.VerdusoftProfile:
            model.VerdusoftProfile = VerdusoftProfileModel(
                GroceryId=user.VerdusoftProfile.GroceryId,
                Role=user.VerdusoftProfile.Role,
            )

        if user.RedVecinaProfile:
            model.RedVecinaProfile = RedVecinaProfileModel(
                UnitId=user.RedVecinaProfile.UnitId,
                BuildingId=user.RedVecinaProfile.BuildingId,
                Role=user.RedVecinaProfile.Role,
            )

        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, user_id: int | str) -> Optional[User]:
        """Get user by ID with profiles and related data loaded."""
        from sqlalchemy.orm import joinedload
        from app.domain.models.profiles import VerdusoftProfile
        
        model = (
            self.db.query(UserModel)
            .options(
                joinedload(UserModel.VerdusoftProfile).joinedload(VerdusoftProfileModel.Grocery),
                joinedload(UserModel.RedVecinaProfile)
            )
            .filter(UserModel.Id == user_id)
            .first()
        )
        return self._to_entity(model) if model else None

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email with Profiles loaded."""
        from sqlalchemy.orm import joinedload
        from app.domain.models.profiles import VerdusoftProfile
        
        model = (
            self.db.query(UserModel)
            .options(
                joinedload(UserModel.VerdusoftProfile).joinedload(VerdusoftProfileModel.Grocery),
                joinedload(UserModel.RedVecinaProfile)
            )
            .filter(UserModel.Email == email)
            .first()
        )
        return self._to_entity(model) if model else None

    def get_all(self) -> List[User]:
        """Get all users."""
        return [self._to_entity(model) for model in self.db.query(UserModel).all()]

    def get_by_grocery_id(self, grocery_id: int) -> List[User]:
        """Get users for a grocery via VerdusoftProfile."""
        from app.domain.models.profiles import VerdusoftProfile
        return [
            self._to_entity(model)
            for model in (
                self.db.query(UserModel)
                .join(VerdusoftProfileModel)
                .filter(VerdusoftProfileModel.GroceryId == grocery_id)
                .all()
            )
        ]

    def update(self, user: User) -> User:
        """Update user."""
        model = self.db.query(UserModel).filter(UserModel.Id == user.Id).first()
        if not model:
            return user
        self._apply_entity(model, user)

        if user.VerdusoftProfile:
            if model.VerdusoftProfile is None:
                model.VerdusoftProfile = VerdusoftProfileModel(
                    GroceryId=user.VerdusoftProfile.GroceryId,
                    Role=user.VerdusoftProfile.Role,
                )
            else:
                model.VerdusoftProfile.GroceryId = user.VerdusoftProfile.GroceryId
                model.VerdusoftProfile.Role = user.VerdusoftProfile.Role

        if user.RedVecinaProfile:
            if model.RedVecinaProfile is None:
                model.RedVecinaProfile = RedVecinaProfileModel(
                    UnitId=user.RedVecinaProfile.UnitId,
                    BuildingId=user.RedVecinaProfile.BuildingId,
                    Role=user.RedVecinaProfile.Role,
                )
            else:
                model.RedVecinaProfile.UnitId = user.RedVecinaProfile.UnitId
                model.RedVecinaProfile.BuildingId = user.RedVecinaProfile.BuildingId
                model.RedVecinaProfile.Role = user.RedVecinaProfile.Role

        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, user_id: int | str) -> bool:
        """Delete user."""
        model = self.db.query(UserModel).filter(UserModel.Id == user_id).first()
        if model:
            self.db.delete(model)
            self.db.commit()
            return True
        return False

    def exists_by_email(self, email: str) -> bool:
        """Check if email exists."""
        return self.db.query(UserModel).filter(UserModel.Email == email).count() > 0

    def count_by_grocery_id(self, grocery_id: int) -> int:
        """Count users in grocery via VerdusoftProfile."""
        from app.domain.models.profiles import VerdusoftProfile
        return (
            self.db.query(UserModel)
            .join(VerdusoftProfileModel)
            .filter(VerdusoftProfileModel.GroceryId == grocery_id)
            .count()
        )
