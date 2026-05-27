from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from reconagent.models import Approval, ReconciliationException
from reconagent.services.audit import AuditService
from reconagent.services.auth import can_decide


DECISION_APPROVED = "approved"
DECISION_REJECTED = "rejected"
ALLOWED_DECISIONS = {DECISION_APPROVED, DECISION_REJECTED}


class ApprovalService:
    def __init__(self) -> None:
        self.audit = AuditService()

    def decide(
        self,
        session: Session,
        approval_id: str,
        *,
        actor_id: str,
        decision: str,
        note: str,
    ) -> Approval:
        approval = session.get(Approval, approval_id)
        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")
        if approval.status != "pending":
            raise HTTPException(status_code=409, detail="Approval is already decided")
        if decision not in ALLOWED_DECISIONS:
            raise HTTPException(status_code=422, detail="Decision must be approved or rejected")
        if not can_decide(actor_id, approval.proposed_action):
            raise HTTPException(status_code=403, detail="Actor cannot decide this approval")

        exception = session.get(ReconciliationException, approval.exception_id)
        approval.status = "completed"
        approval.decision = decision
        approval.decided_by = actor_id
        approval.decided_at = datetime.now(UTC)
        approval.note = note
        if exception:
            exception.status = DECISION_APPROVED if decision == DECISION_APPROVED else DECISION_REJECTED

        self.audit.append_event(
            session,
            entity_type="approval",
            entity_id=approval.id,
            actor_id=actor_id,
            action=f"approval_{decision}",
            payload={
                "exception_id": approval.exception_id,
                "proposed_action": approval.proposed_action,
                "decision": decision,
                "note": note,
            },
            run_id=exception.run_id if exception else None,
        )
        session.commit()
        return approval
