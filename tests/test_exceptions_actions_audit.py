from datetime import date

import pytest
from sqlalchemy import select

from reconagent.models import Approval, Invoice, Payment, Vendor
from reconagent.services.approvals import ApprovalService
from reconagent.services.audit import AuditService
from reconagent.services.exceptions import ExceptionDetector
from reconagent.services.matching import MatchingEngine


def test_exception_detector_finds_duplicate_payment_missing_po_and_changed_bank_account():
    vendor = Vendor(id="vendor-1", name="Acme GmbH", normalized_name="acme gmbh")
    invoice = Invoice(
        id="inv-1",
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        invoice_number="INV-001",
        amount_cents=500000,
        currency="EUR",
        invoice_date=date(2026, 5, 1),
        due_date=date(2026, 5, 31),
        po_number=None,
        bank_account="DE-OLD",
        source_hash="hash",
        raw_payload="{}",
    )
    payment_1 = Payment(
        id="pay-1",
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        amount_cents=500000,
        currency="EUR",
        payment_date=date(2026, 5, 2),
        bank_account="DE-NEW",
        reference="INV-001",
        source_hash="hash",
        raw_payload="{}",
    )
    payment_2 = Payment(
        id="pay-2",
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        amount_cents=500000,
        currency="EUR",
        payment_date=date(2026, 5, 3),
        bank_account="DE-NEW",
        reference="INV-001 duplicate",
        source_hash="hash",
        raw_payload="{}",
    )

    match = MatchingEngine().find_best_match(invoice, [payment_1, payment_2], [])
    exceptions = ExceptionDetector().detect_for_invoice(invoice, match, [payment_1, payment_2])
    types = {exception.exception_type for exception in exceptions}

    assert {"missing_po", "changed_bank_account", "duplicate_payment"}.issubset(types)


def test_duplicate_payment_detection_ignores_same_amount_in_different_currency():
    vendor = Vendor(id="vendor-1", name="Acme GmbH", normalized_name="acme gmbh")
    invoice = Invoice(
        id="inv-1",
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        invoice_number="INV-001",
        amount_cents=500000,
        currency="EUR",
        invoice_date=date(2026, 5, 1),
        due_date=date(2026, 5, 31),
        po_number="PO-1",
        bank_account="DE-OLD",
        source_hash="invoice-hash",
        raw_payload="{}",
    )
    eur_payment = Payment(
        id="pay-1",
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        amount_cents=500000,
        currency="EUR",
        payment_date=date(2026, 5, 2),
        bank_account="DE-OLD",
        reference="INV-001",
        source_hash="payment-hash-1",
        raw_payload="{}",
    )
    usd_payment = Payment(
        id="pay-2",
        vendor_id=vendor.id,
        vendor_name=vendor.name,
        amount_cents=500000,
        currency="USD",
        payment_date=date(2026, 5, 3),
        bank_account="DE-OLD",
        reference="INV-001",
        source_hash="payment-hash-2",
        raw_payload="{}",
    )

    match = MatchingEngine().find_best_match(invoice, [eur_payment, usd_payment], [])
    exceptions = ExceptionDetector().detect_for_invoice(
        invoice,
        match,
        [eur_payment, usd_payment],
    )

    assert "duplicate_payment" not in {exception.exception_type for exception in exceptions}


def test_audit_hash_chain_links_events(db_session):
    audit = AuditService()

    first = audit.append_event(
        db_session,
        entity_type="demo",
        entity_id="1",
        actor_id="system",
        action="created",
        payload={"value": 1},
    )
    second = audit.append_event(
        db_session,
        entity_type="demo",
        entity_id="2",
        actor_id="system",
        action="created",
        payload={"value": 2},
    )

    assert first.previous_hash == "0" * 64
    assert second.previous_hash == first.event_hash
    assert second.event_hash != first.event_hash


def test_analyst_cannot_approve_high_risk_action(client, db_session):
    response = client.post(
        "/api/v1/imports/invoices",
        files={
            "file": (
                "invoices.csv",
                b"vendor_name,invoice_number,amount,currency,invoice_date,due_date,po_number,bank_account\n"
                b"Acme GmbH,INV-001,1000.00,EUR,2026-05-01,2026-05-31,,DE-OLD\n",
                "text/csv",
            )
        },
    )
    assert response.status_code == 200
    client.post(
        "/api/v1/imports/payments",
        files={
            "file": (
                "payments.csv",
                b"vendor_name,amount,currency,payment_date,bank_account,reference\n"
                b"Acme GmbH,950.00,EUR,2026-05-02,DE-NEW,INV-001\n",
                "text/csv",
            )
        },
    )
    client.post(
        "/api/v1/imports/policies",
        files={
            "file": (
                "policies.csv",
                b"title,body,risk_level\n"
                b"Payment controls,Amount mismatches and changed bank accounts must be held for review.,high\n",
                "text/csv",
            )
        },
    )
    run = client.post("/api/v1/reconciliation-runs").json()
    approval = db_session.scalar(
        select(Approval).where(
            Approval.status == "pending",
            Approval.proposed_action.in_(["hold_for_review", "escalate_to_controller"]),
        )
    )

    decision = client.post(
        f"/api/v1/approvals/{approval.id}/decision",
        json={"actor_id": "analyst", "decision": "approved", "note": "looks fine"},
    )

    assert run["status"] == "completed"
    assert decision.status_code == 403

    allowed = client.post(
        f"/api/v1/approvals/{approval.id}/decision",
        json={"actor_id": "controller", "decision": "approved", "note": "reviewed"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["status"] == "completed"
