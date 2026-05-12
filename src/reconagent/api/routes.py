from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from reconagent.config import get_settings
from reconagent.database import get_session
from reconagent.models import Approval, AuditEvent, ReconciliationException, ReconciliationRun
from reconagent.schemas import (
    ApprovalDecisionRequest,
    ApprovalRead,
    AuditEventRead,
    ExceptionRead,
    ImportResponse,
    MetricsSummary,
    ReconciliationRunCreate,
    ReconciliationRunRead,
)
from reconagent.services.approvals import ApprovalService
from reconagent.services.imports import (
    import_invoices,
    import_ledger_entries,
    import_payments,
    import_policies,
)
from reconagent.services.metrics import metrics_summary
from reconagent.services.reconciliation import ReconciliationService
from reconagent.workers.jobs import enqueue_reconciliation_run

router = APIRouter(prefix="/api/v1")


@router.post("/imports/invoices", response_model=ImportResponse)
async def import_invoice_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> ImportResponse:
    ids = import_invoices(session, await file.read())
    return ImportResponse(imported=len(ids), ids=ids)


@router.post("/imports/payments", response_model=ImportResponse)
async def import_payment_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> ImportResponse:
    ids = import_payments(session, await file.read())
    return ImportResponse(imported=len(ids), ids=ids)


@router.post("/imports/ledger-entries", response_model=ImportResponse)
async def import_ledger_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> ImportResponse:
    ids = import_ledger_entries(session, await file.read())
    return ImportResponse(imported=len(ids), ids=ids)


@router.post("/imports/policies", response_model=ImportResponse)
async def import_policy_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> ImportResponse:
    ids = import_policies(session, await file.read())
    return ImportResponse(imported=len(ids), ids=ids)


@router.post("/reconciliation-runs", response_model=ReconciliationRunRead)
def create_reconciliation_run(
    _: ReconciliationRunCreate = ReconciliationRunCreate(),
    session: Session = Depends(get_session),
) -> ReconciliationRun:
    run = ReconciliationService().create_run(session)
    if get_settings().use_rq:
        enqueue_reconciliation_run(run.id)
    else:
        ReconciliationService().process_run(session, run.id)
    session.refresh(run)
    return run


@router.get("/reconciliation-runs/{run_id}", response_model=ReconciliationRunRead)
def get_reconciliation_run(
    run_id: str,
    session: Session = Depends(get_session),
) -> ReconciliationRun | None:
    return session.get(ReconciliationRun, run_id)


@router.get("/exceptions", response_model=list[ExceptionRead])
def list_exceptions(
    run_id: str | None = None,
    session: Session = Depends(get_session),
) -> list[ReconciliationException]:
    query = select(ReconciliationException)
    if run_id:
        query = query.where(ReconciliationException.run_id == run_id)
    return list(session.scalars(query))


@router.post("/approvals/{approval_id}/decision", response_model=ApprovalRead)
def decide_approval(
    approval_id: str,
    request: ApprovalDecisionRequest,
    session: Session = Depends(get_session),
) -> Approval:
    return ApprovalService().decide(
        session,
        approval_id,
        actor_id=request.actor_id,
        decision=request.decision,
        note=request.note,
    )


@router.get("/audit-events", response_model=list[AuditEventRead])
def list_audit_events(
    run_id: str | None = None,
    session: Session = Depends(get_session),
) -> list[AuditEvent]:
    query = select(AuditEvent).order_by(AuditEvent.created_at, AuditEvent.id)
    if run_id:
        query = query.where(AuditEvent.run_id == run_id)
    return list(session.scalars(query))


@router.get("/metrics/summary", response_model=MetricsSummary)
def get_metrics_summary(session: Session = Depends(get_session)) -> MetricsSummary:
    return metrics_summary(session)
