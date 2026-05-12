from sqlalchemy import select

from reconagent.models import AuditEvent, ReconciliationException, ReconciliationMatch


def test_full_api_flow_imports_reconciles_exceptions_and_audit(client, db_session):
    uploads = [
        (
            "/api/v1/imports/invoices",
            b"vendor_name,invoice_number,amount,currency,invoice_date,due_date,po_number,bank_account\n"
            b"Acme GmbH,INV-001,1000.00,EUR,2026-05-01,2026-05-31,PO-1,DE123\n"
            b"Beta BV,INV-002,5000.00,EUR,2026-04-01,2026-04-30,,NL111\n",
        ),
        (
            "/api/v1/imports/payments",
            b"vendor_name,amount,currency,payment_date,bank_account,reference\n"
            b"Acme GmbH,1000.00,EUR,2026-05-03,DE123,INV-001\n"
            b"Beta BV,5000.00,EUR,2026-04-04,NL222,INV-002\n"
            b"Beta BV,5000.00,EUR,2026-04-05,NL222,INV-002 DUP\n",
        ),
        (
            "/api/v1/imports/ledger-entries",
            b"vendor_name,amount,currency,entry_date,account_code,description,reference\n"
            b"Acme GmbH,1000.00,EUR,2026-05-02,2000,Invoice booked,INV-001\n",
        ),
        (
            "/api/v1/imports/policies",
            b"title,body,risk_level\n"
            b"Duplicate payment policy,Duplicate payments inside seven days must be held for review.,high\n"
            b"PO policy,Invoices without purchase orders require a document request before payment.,medium\n",
        ),
    ]
    for path, content in uploads:
        response = client.post(path, files={"file": ("data.csv", content, "text/csv")})
        assert response.status_code == 200

    run_response = client.post("/api/v1/reconciliation-runs")
    run = run_response.json()

    assert run_response.status_code == 200
    assert run["status"] == "completed"
    assert db_session.scalars(select(ReconciliationMatch)).all()

    exceptions_response = client.get(f"/api/v1/exceptions?run_id={run['id']}")
    exception_types = {item["exception_type"] for item in exceptions_response.json()}
    assert {"missing_po", "duplicate_payment", "changed_bank_account"}.issubset(exception_types)

    audit_events = db_session.scalars(select(AuditEvent).order_by(AuditEvent.created_at)).all()
    assert len(audit_events) >= 3
    assert audit_events[0].previous_hash == "0" * 64
    assert all(event.event_hash for event in audit_events)

    summary = client.get("/api/v1/metrics/summary").json()
    assert summary["completed_runs"] == 1
    assert summary["pending_approvals"] >= 1

    db_exceptions = db_session.scalars(select(ReconciliationException)).all()
    assert all(exception.policy_citation for exception in db_exceptions)
