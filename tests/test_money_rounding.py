from decimal import Decimal

import pytest

from app_base.shared_kernel.contracts.payments import PaymentIntentCommand
from app_base.shared_kernel.money import ceil_xof, floor_available_xof, normalize_money_tree


def test_xof_amounts_are_ceiled_without_float_rounding():
    assert ceil_xof(1500) == 1500
    assert ceil_xof("1500.01") == 1501
    assert ceil_xof(Decimal("1500.8")) == 1501


def test_available_balances_are_floored():
    assert floor_available_xof("1500.99") == 1500
    assert floor_available_xof(Decimal("1500.01")) == 1500


def test_money_tree_preserves_the_balance_safety_rule():
    payload = normalize_money_tree({"amount": "10.1", "available_balance": "9.9", "nested": {"fee": 1.2}})
    assert payload == {"amount": 11, "available_balance": 9, "nested": {"fee": 2}}


def test_payment_contract_normalizes_decimal_amounts_before_transport():
    command = PaymentIntentCommand(
        checkout_id="checkout-1",
        business_reference="diddishop:checkout:checkout-1",
        amount_minor="5640.01",
        idempotency_key="payment-1",
        customer_phone="+2250700000000",
    )
    assert command.amount_minor == 5641


@pytest.mark.parametrize("value", ["NaN", "Infinity", -1, "-0.1", True])
def test_invalid_money_values_are_rejected(value):
    with pytest.raises(ValueError):
        ceil_xof(value)
