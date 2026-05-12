from datetime import date

from reconagent.domain.money import cents_to_decimal, parse_amount_to_cents
from reconagent.domain.normalization import normalize_invoice_row, normalize_name, normalize_reference


def test_money_is_parsed_to_integer_minor_units():
    assert parse_amount_to_cents("1,234.56") == 123456
    assert cents_to_decimal(123456).as_tuple().exponent == -2


def test_vendor_and_reference_normalization_removes_format_noise():
    assert normalize_name(" ACME, GmbH ") == "acme gmbh"
    assert normalize_reference("INV-2026/001") == "inv2026001"


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
