"""
User Repository Port (Interface).
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.user import User


class UserRepositoryPort(ABC):
    """Abstract interface for User persistence operations."""

    @abstractmethod
    def create(self, user: User) -> User:
        """Create a new user and return with generated ID."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: int | str) -> Optional[User]:
        """Get user by ID."""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        pass

    @abstractmethod
    def get_all(self) -> List[User]:
        """Get all users."""
        pass

    @abstractmethod
    def get_by_grocery_id(self, grocery_id: int) -> List[User]:
        """Get all users for a grocery."""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Update an existing user."""
        pass

    @abstractmethod
    def delete(self, user_id: int | str) -> bool:
        """Delete a user. Returns True if successful."""
        pass

    @abstractmethod
    def exists_by_email(self, email: str) -> bool:
        """Check if email already exists."""
        pass

    @abstractmethod
    def count_by_grocery_id(self, grocery_id: int) -> int:
        """Count users in a grocery."""
        pass
