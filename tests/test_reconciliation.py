from datetime import date

import pytest
from sqlalchemy import select

from reconagent.models import AuditEvent, Invoice, ReconciliationMatch, ReconciliationRun, Vendor
from reconagent.services.reconciliation import ReconciliationService


class FailingDetector:
    def detect_for_invoice(self, *_args, **_kwargs):
        raise RuntimeError("detector exploded")

    def detect_unmatched_ledger_entries(self, *_args, **_kwargs):
        return []


def test_failed_reconciliation_run_does_not_commit_partial_matches(db_session):
    vendor = Vendor(name="Acme GmbH", normalized_name="acme gmbh")
    run = ReconciliationRun(status="queued")
    db_session.add_all([vendor, run])
    db_session.flush()
    db_session.add(
        Invoice(
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            invoice_number="INV-001",
            amount_cents=100000,
            currency="EUR",
            invoice_date=date(2026, 5, 1),
            due_date=date(2026, 5, 31),
            source_hash="invoice-hash",
            raw_payload="{}",
        )
    )
    db_session.commit()

    service = ReconciliationService()
    service.detector = FailingDetector()

    with pytest.raises(RuntimeError, match="detector exploded"):
        service.process_run(db_session, run.id)

    db_session.refresh(run)
    matches = db_session.scalars(
        select(ReconciliationMatch).where(ReconciliationMatch.run_id == run.id)
    ).all()
    failed_events = db_session.scalars(
        select(AuditEvent).where(
            AuditEvent.run_id == run.id,
            AuditEvent.action == "run_failed",
        )
    ).all()

    assert run.status == "failed"
    assert matches == []
    assert len(failed_events) == 1
