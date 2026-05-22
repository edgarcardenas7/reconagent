from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, select

from reconagent.models import Invoice, LedgerEntry, Payment, Vendor
from reconagent.services.imports import import_invoices, import_ledger_entries, import_payments


def test_invoice_import_is_idempotent_by_source_hash(db_session):
    content = (
        b"vendor_name,invoice_number,amount,currency,invoice_date,due_date,po_number,bank_account\n"
        b"Acme GmbH,INV-001,1000.00,EUR,2026-05-01,2026-05-31,PO-1,DE123\n"
    )

    first_import_ids = import_invoices(db_session, content)
    second_import_ids = import_invoices(db_session, content)

    invoice_count = db_session.scalar(select(func.count()).select_from(Invoice))

    assert len(first_import_ids) == 1
    assert second_import_ids == []
    assert invoice_count == 1


def test_payment_import_is_idempotent_by_source_hash(db_session):
    content = (
        b"vendor_name,amount,currency,payment_date,bank_account,reference\n"
        b"Acme GmbH,1000.00,EUR,2026-05-03,DE123,INV-001\n"
    )

    first_import_ids = import_payments(db_session, content)
    second_import_ids = import_payments(db_session, content)

    payment_count = db_session.scalar(select(func.count()).select_from(Payment))

    assert len(first_import_ids) == 1
    assert second_import_ids == []
    assert payment_count == 1


def test_ledger_import_is_idempotent_by_source_hash(db_session):
    content = (
        b"vendor_name,amount,currency,entry_date,account_code,description,reference\n"
        b"Acme GmbH,1000.00,EUR,2026-05-02,2000,Invoice booked,INV-001\n"
    )

    first_import_ids = import_ledger_entries(db_session, content)
    second_import_ids = import_ledger_entries(db_session, content)

    ledger_count = db_session.scalar(select(func.count()).select_from(LedgerEntry))

    assert len(first_import_ids) == 1
    assert second_import_ids == []
    assert ledger_count == 1


def test_invoice_source_hash_is_unique_at_database_level(db_session):
    vendor = Vendor(name="Acme GmbH", normalized_name="acme gmbh")
    db_session.add(vendor)
    db_session.flush()

    first_invoice = Invoice(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        invoice_number="INV-001",
        amount_cents=100000,
        currency="EUR",
        invoice_date=date(2026, 5, 1),
        due_date=date(2026, 5, 31),
        source_hash="same-source-hash",
        raw_payload="{}",
    )
    second_invoice = Invoice(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        invoice_number="INV-001",
        amount_cents=100000,
        currency="EUR",
        invoice_date=date(2026, 5, 1),
        due_date=date(2026, 5, 31),
        source_hash="same-source-hash",
        raw_payload="{}",
    )

    db_session.add(first_invoice)
    db_session.commit()
    db_session.add(second_invoice)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_payment_source_hash_is_unique_at_database_level(db_session):
    vendor = Vendor(name="Acme GmbH", normalized_name="acme gmbh")
    db_session.add(vendor)
    db_session.flush()

    first_payment = Payment(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        amount_cents=100000,
        currency="EUR",
        payment_date=date(2026, 5, 3),
        bank_account="DE123",
        reference="INV-001",
        source_hash="same-source-hash",
        raw_payload="{}",
    )
    second_payment = Payment(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        amount_cents=100000,
        currency="EUR",
        payment_date=date(2026, 5, 3),
        bank_account="DE123",
        reference="INV-001",
        source_hash="same-source-hash",
        raw_payload="{}",
    )

    db_session.add(first_payment)
    db_session.commit()
    db_session.add(second_payment)

    with pytest.raises(IntegrityError):
        db_session.commit()


def test_ledger_source_hash_is_unique_at_database_level(db_session):
    vendor = Vendor(name="Acme GmbH", normalized_name="acme gmbh")
    db_session.add(vendor)
    db_session.flush()

    first_entry = LedgerEntry(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        amount_cents=100000,
        currency="EUR",
        account_code="2000",
        entry_date=date(2026, 5, 2),
        description="Invoice booked",
        reference="INV-001",
        source_hash="same-source-hash",
        raw_payload="{}",
    )
    second_entry = LedgerEntry(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        amount_cents=100000,
        currency="EUR",
        account_code="2000",
        entry_date=date(2026, 5, 2),
        description="Invoice booked",
        reference="INV-001",
        source_hash="same-source-hash",
        raw_payload="{}",
    )

    db_session.add(first_entry)
    db_session.commit()
    db_session.add(second_entry)

    with pytest.raises(IntegrityError):
        db_session.commit()
