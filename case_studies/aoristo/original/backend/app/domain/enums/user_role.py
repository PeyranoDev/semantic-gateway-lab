"""
User role enum.
"""
from enum import Enum


class GroceryRole(int, Enum):
    """
    User roles for authorization.
    Values match .NET GroceryRole enum for compatibility.
    """
    STAFF = 1
    ADMIN = 2
    SUPER_ADMIN = 3
    
    @classmethod
    def from_string(cls, role_str: str) -> "GroceryRole":
        """Convert string to enum."""
        mapping = {
            "staff": cls.STAFF,
            "admin": cls.ADMIN,
            "superadmin": cls.SUPER_ADMIN,
            "super_admin": cls.SUPER_ADMIN,
        }
        return mapping.get(role_str.lower(), cls.STAFF)
    
    def to_string(self) -> str:
        """Convert enum to display string."""
        mapping = {
            self.STAFF: "Staff",
            self.ADMIN: "Admin",
            self.SUPER_ADMIN: "SuperAdmin",
        }
        return mapping.get(self, "Staff")
