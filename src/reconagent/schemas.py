from datetime import datetime

from pydantic import BaseModel, Field


class ImportResponse(BaseModel):
    imported: int
    ids: list[str]


class ReconciliationRunCreate(BaseModel):
    run_all_imported_records: bool = True


class ReconciliationRunRead(BaseModel):
    id: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    error: str | None

    model_config = {"from_attributes": True}


class ExceptionRead(BaseModel):
    id: str
    run_id: str
    invoice_id: str | None
    payment_id: str | None
    ledger_entry_id: str | None
    exception_type: str
    severity: str
    explanation: str
    proposed_action: str
    policy_citation: str
    requires_approval: bool
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalDecisionRequest(BaseModel):
    actor_id: str = Field(..., examples=["controller"])
    decision: str = Field(..., pattern="^(approved|rejected)$")
    note: str = ""


class ApprovalRead(BaseModel):
    id: str
    exception_id: str
    proposed_action: str
    status: str
    decision: str | None
    decided_by: str | None
    decided_at: datetime | None
    note: str | None

    model_config = {"from_attributes": True}


class AuditEventRead(BaseModel):
    id: str
    run_id: str | None
    entity_type: str
    entity_id: str
    actor_id: str
    action: str
    previous_hash: str
    event_hash: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricsSummary(BaseModel):
    runs_total: int
    completed_runs: int
    open_exceptions: int
    pending_approvals: int
    approvals_completed: int
