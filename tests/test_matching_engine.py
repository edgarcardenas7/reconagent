from datetime import date

from reconagent.models import Invoice, LedgerEntry, Payment, Vendor
from reconagent.services.matching import MatchingEngine


def make_vendor() -> Vendor:
    return Vendor(id="vendor-1", name="Acme GmbH", normalized_name="acme gmbh")


def test_exact_invoice_payment_ledger_match_scores_above_threshold():
    vendor = make_vendor()
    invoice = Invoice(
        id="inv-1",
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        invoice_number="INV-001",
        amount_cents=100000,
        currency="EUR",
        invoice_date=date(2026, 5, 1),
        due_date=date(2026, 5, 31),
        po_number="PO-1",
        bank_account="DE123",
        source_hash="hash",
        raw_payload="{}",
    )
    payment = Payment(
        id="pay-1",
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        amount_cents=100000,
        currency="EUR",
        payment_date=date(2026, 5, 3),
        bank_account="DE123",
        reference="Payment for INV-001",
        source_hash="hash",
        raw_payload="{}",
    )
    ledger = LedgerEntry(
        id="ledger-1",
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        amount_cents=100000,
        currency="EUR",
        account_code="2000",
        entry_date=date(2026, 5, 2),
        description="Invoice booked",
        reference="INV-001",
        source_hash="hash",
        raw_payload="{}",
    )

    result = MatchingEngine().find_best_match(invoice, [payment], [ledger])

    assert result.status == "matched"
    assert result.score == 100
    assert result.payment == payment
    assert result.ledger_entry == ledger


def test_amount_mismatch_keeps_match_but_lowers_score():
    vendor = make_vendor()
    invoice = Invoice(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        invoice_number="INV-002",
        amount_cents=100000,
        currency="EUR",
        invoice_date=date(2026, 5, 1),
        due_date=date(2026, 5, 31),
        po_number="PO-1",
        source_hash="hash",
        raw_payload="{}",
    )
    payment = Payment(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        amount_cents=98000,
        currency="EUR",
        payment_date=date(2026, 5, 2),
        bank_account="DE123",
        reference="INV-002",
        source_hash="hash",
        raw_payload="{}",
    )

    result = MatchingEngine().find_best_match(invoice, [payment], [])

    assert result.status == "matched"
    assert result.components["amount_match"] == 20
