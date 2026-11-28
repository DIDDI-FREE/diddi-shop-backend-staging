"""Single rounding policy for all XOF values crossing the Shop boundary."""

from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, InvalidOperation
from typing import Annotated

from pydantic import BeforeValidator


def _decimal(value: object) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError("monetary value must be numeric")
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("monetary value must be numeric") from exc
    if not decimal.is_finite():
        raise ValueError("monetary value must be finite")
    return decimal


def ceil_xof(value: object) -> int:
    """Round a non-negative XOF amount upward to an integer."""
    decimal = _decimal(value)
    if decimal < 0:
        raise ValueError("monetary value must be non-negative")
    return int(decimal.to_integral_value(rounding=ROUND_CEILING))


def floor_available_xof(value: object) -> int:
    """Round an available balance downward to avoid over-disbursement."""
    decimal = _decimal(value)
    if decimal < 0:
        raise ValueError("available balance must be non-negative")
    return int(decimal.to_integral_value(rounding=ROUND_FLOOR))


def normalize_money_fields(payload: dict, *field_names: str) -> dict:
    """Copy a payload while normalizing only explicitly monetary fields."""
    normalized = dict(payload)
    for field_name in field_names:
        if field_name in normalized and normalized[field_name] is not None:
            normalized[field_name] = ceil_xof(normalized[field_name])
    return normalized


XofAmount = Annotated[int, BeforeValidator(ceil_xof)]


_CEILING_KEYS = {
    "amount", "amount_minor", "amount_to_refund", "applied_discount_minor",
    "client_paid_minor", "declared_value", "delivery_fee", "delivery_fee_minor",
    "discount_amount_minor", "discount_minor", "diddi_contribution_minor",
    "final_amount_minor", "fee_amount", "fee", "line_total_minor", "price_minor",
    "professional_payout_minor", "quoted_price", "refund_amount", "subtotal_minor",
    "total_minor", "unit_price_minor", "requested_amount_minor", "reserved_amount_minor",
}
_FLOOR_KEYS = {"available_balance", "available_balance_minor", "balance_available"}


def normalize_money_tree(value: object) -> object:
    """Normalize known money keys in a persisted or external JSON tree."""
    if isinstance(value, list):
        return [normalize_money_tree(item) for item in value]
    if not isinstance(value, dict):
        return value
    normalized = {}
    for key, item in value.items():
        if key in _FLOOR_KEYS and item is not None:
            normalized[key] = floor_available_xof(item)
        elif key in _CEILING_KEYS and item is not None:
            normalized[key] = ceil_xof(item)
        else:
            normalized[key] = normalize_money_tree(item)
    return normalized
