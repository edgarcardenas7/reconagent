from datetime import date

from reconagent.models import (
    Approval,
    AuditEvent,
    Invoice,
    Payment,
    ReconciliationException,
    ReconciliationMatch,
    ReconciliationRun,
    Vendor,
)


def test_vendor_groups_financial_records_under_one_identity(db_session):
    vendor = Vendor(name="AWS Europe", normalized_name="aws europe")
    db_session.add(vendor)
    db_session.flush()

    invoice = Invoice(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        invoice_number="INV-1",
        amount_cents=1999,
        currency="EUR",
        invoice_date=date(2026, 5, 1),
        due_date=date(2026, 5, 31),
        source_hash="invoice-hash",
        raw_payload="{}",
    )
    payment = Payment(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        amount_cents=1999,
        currency="EUR",
        payment_date=date(2026, 5, 3),
        bank_account="DE123",
        reference="INV-1",
        source_hash="payment-hash",
        raw_payload="{}",
    )
    db_session.add_all([invoice, payment])
    db_session.commit()

    stored_vendor = db_session.get(Vendor, vendor.id)

    assert stored_vendor.normalized_name == "aws europe"
    assert stored_vendor.invoices[0].invoice_number == "INV-1"
    assert stored_vendor.payments[0].reference == "INV-1"


def test_reconciliation_run_owns_results_exceptions_and_audit_events(db_session):
    vendor = Vendor(name="Acme GmbH", normalized_name="acme gmbh")
    run = ReconciliationRun(status="completed")
    db_session.add_all([vendor, run])
    db_session.flush()

    invoice = Invoice(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        invoice_number="INV-2",
        amount_cents=500000,
        currency="EUR",
        invoice_date=date(2026, 5, 1),
        due_date=date(2026, 5, 31),
        source_hash="invoice-hash",
        raw_payload="{}",
    )
    payment = Payment(
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        amount_cents=500000,
        currency="EUR",
        payment_date=date(2026, 5, 2),
        bank_account="DE123",
        reference="INV-2",
        source_hash="payment-hash",
        raw_payload="{}",
    )
    db_session.add_all([invoice, payment])
    db_session.flush()

    match = ReconciliationMatch(
        run_id=run.id,
        invoice_id=invoice.id,
        payment_id=payment.id,
        score=95,
        score_components='{"vendor_match":35}',
        status="matched",
    )
    exception = ReconciliationException(
        run_id=run.id,
        invoice_id=invoice.id,
        payment_id=payment.id,
        exception_type="missing_po",
        severity="medium",
        explanation="Invoice has no purchase order.",
        proposed_action="request_document",
        policy_citation="PO policy",
        requires_approval=True,
        status="awaiting_approval",
    )
    db_session.add_all([match, exception])
    db_session.flush()

    approval = Approval(
        exception_id=exception.id,
        proposed_action="request_document",
        status="pending",
    )
    audit_event = AuditEvent(
        run_id=run.id,
        entity_type="reconciliation_exception",
        entity_id=exception.id,
        actor_id="system",
        action="exception_detected",
        payload_json="{}",
        previous_hash="0" * 64,
        event_hash="1" * 64,
    )
    db_session.add_all([approval, audit_event])
    db_session.commit()

    stored_run = db_session.get(ReconciliationRun, run.id)
    stored_exception = db_session.get(ReconciliationException, exception.id)

    assert stored_run.matches[0].score == 95
    assert stored_run.exceptions[0].exception_type == "missing_po"
    assert stored_run.audit_events[0].action == "exception_detected"
    assert stored_exception.approvals[0].status == "pending"
