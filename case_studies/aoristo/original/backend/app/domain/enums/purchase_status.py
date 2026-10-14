"""
Purchase status enum.
"""
from enum import Enum


class PurchaseStatus(str, Enum):
    """Purchase/restock transaction status."""
    PENDING = "pendiente"
    RECEIVED = "recibida"
    CANCELLED = "cancelada"
