import pytest
from fastapi import HTTPException

from reconagent.models import Approval, ReconciliationException, ReconciliationRun
from reconagent.services.approvals import ApprovalService


def test_approval_service_rejects_unknown_decision(db_session):
    run = ReconciliationRun(status="completed")
    db_session.add(run)
    db_session.flush()

    exception = ReconciliationException(
        run_id=run.id,
        exception_type="missing_po",
        severity="medium",
        explanation="Invoice has no purchase order.",
        proposed_action="request_document",
        policy_citation="PO policy",
        requires_approval=True,
        status="awaiting_approval",
    )
    db_session.add(exception)
    db_session.flush()

    approval = Approval(
        exception_id=exception.id,
        proposed_action="request_document",
        status="pending",
    )
    db_session.add(approval)
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        ApprovalService().decide(
            db_session,
            approval.id,
            actor_id="analyst",
            decision="maybe",
            note="not a real decision",
        )

    db_session.refresh(approval)
    db_session.refresh(exception)

    assert exc_info.value.status_code == 422
    assert approval.status == "pending"
    assert approval.decision is None
    assert exception.status == "awaiting_approval"
