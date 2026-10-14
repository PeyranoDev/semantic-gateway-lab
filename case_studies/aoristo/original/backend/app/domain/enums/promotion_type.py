"""
Promotion type enum.
"""
from enum import Enum

# Only these types can be used when creating new promotions
VALID_NEW_TYPES = frozenset([
    "BUY_X_PAY_Y",
    "VOLUME_PRICING",
    "DIRECT_DISCOUNT",
    "COMBO_BUNDLE",
])


class PromotionType(str, Enum):
    """Promotion/discount types — V2."""

    # ── New types (V2) ──
    BUY_X_PAY_Y = "BUY_X_PAY_Y"            # Llevá 3 pagá 2
    VOLUME_PRICING = "VOLUME_PRICING"        # 2kg x $6000 (pro-rata)
    DIRECT_DISCOUNT = "DIRECT_DISCOUNT"      # 15% OFF or $500 OFF
    COMBO_BUNDLE = "COMBO_BUNDLE"            # Multi-product bundle at fixed price

    # ── Legacy types (kept for backward compat with existing DB rows) ──
    PERCENT_DISCOUNT = "PERCENT_DISCOUNT"
    BUY_X_GET_Y = "BUY_X_GET_Y"
    FIXED_DISCOUNT = "FIXED_DISCOUNT"
    QUANTITY_DISCOUNT = "QUANTITY_DISCOUNT"
    PAYMENT_METHOD = "PAYMENT_METHOD"
    COMBO_PRICE = "COMBO_PRICE"
