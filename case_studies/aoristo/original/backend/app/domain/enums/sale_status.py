"""
Sale status enum.
"""
from enum import Enum


class SaleStatus(str, Enum):
    """Sale transaction status."""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
