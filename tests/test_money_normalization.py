from datetime import date
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

import pytest

from reconagent.domain.money import (
    cents_to_decimal,
    decimal_to_cents,
    format_cents,
    parse_amount_to_cents,
)
from reconagent.domain.normalization import (
    normalize_currency,
    normalize_invoice_row,
    normalize_name,
    normalize_reference,
)


def test_money_is_parsed_to_integer_minor_units():
    assert parse_amount_to_cents("1,234.56") == 123456
    assert cents_to_decimal(123456).as_tuple().exponent == -2
    assert format_cents(123456) == "1234.56"


def test_money_rejects_invalid_or_ambiguous_amounts():
    with pytest.raises(ValueError, match="at most two decimal places"):
        parse_amount_to_cents("10.999")
    with pytest.raises(ValueError, match="cannot be empty"):
        parse_amount_to_cents("")
    with pytest.raises(ValueError, match="cannot be negative"):
        parse_amount_to_cents("-1.00")


def test_decimal_to_cents_rounds_intermediate_financial_calculations_explicitly():
    tax_amount = Decimal("19.99") * Decimal("0.21")

    assert tax_amount == Decimal("4.1979")
    assert decimal_to_cents(tax_amount, rounding=ROUND_HALF_UP) == 420
    assert decimal_to_cents(tax_amount, rounding=ROUND_DOWN) == 419


def test_vendor_and_reference_normalization_removes_format_noise():
    assert normalize_name(" ACME, GmbH ") == "acme gmbh"
    assert normalize_reference("INV-2026/001") == "inv2026001"


def test_currency_normalization_requires_three_letters():
    assert normalize_currency(" eur ") == "EUR"
    with pytest.raises(ValueError, match="ISO-4217"):
        normalize_currency("EU")
    with pytest.raises(ValueError, match="ISO-4217"):
        normalize_currency("EU1")


def test_invoice_row_normalization_keeps_money_as_cents():
    row = {
        "vendor_name": "Acme GmbH",
        "invoice_number": "INV-001",
        "amount": "1000.00",
        "currency": "eur",
        "invoice_date": "2026-05-01",
        "due_date": "2026-05-31",
        "po_number": "PO-1",
        "bank_account": "DE123",
    }

    normalized = normalize_invoice_row(row)

    assert normalized["amount_cents"] == 100000
    assert normalized["currency"] == "EUR"
    assert normalized["invoice_date"] == date(2026, 5, 1)
