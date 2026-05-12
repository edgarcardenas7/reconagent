from sqlalchemy import func, select
from sqlalchemy.orm import Session

from reconagent.models import Approval, ReconciliationException, ReconciliationRun
from reconagent.schemas import MetricsSummary


def metrics_summary(session: Session) -> MetricsSummary:
    runs_total = session.scalar(select(func.count()).select_from(ReconciliationRun)) or 0
    completed_runs = (
        session.scalar(
            select(func.count())
            .select_from(ReconciliationRun)
            .where(ReconciliationRun.status == "completed")
        )
        or 0
    )
    open_exceptions = (
        session.scalar(
            select(func.count())
            .select_from(ReconciliationException)
            .where(ReconciliationException.status.in_(["open", "awaiting_approval"]))
        )
        or 0
    )
    pending_approvals = (
        session.scalar(select(func.count()).select_from(Approval).where(Approval.status == "pending"))
        or 0
    )
    approvals_completed = (
        session.scalar(
            select(func.count()).select_from(Approval).where(Approval.status == "completed")
        )
        or 0
    )
    return MetricsSummary(
        runs_total=runs_total,
        completed_runs=completed_runs,
        open_exceptions=open_exceptions,
        pending_approvals=pending_approvals,
        approvals_completed=approvals_completed,
    )
