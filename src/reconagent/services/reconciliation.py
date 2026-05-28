from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from reconagent.models import (
    Approval,
    Invoice,
    LedgerEntry,
    Payment,
    ReconciliationException,
    ReconciliationMatch,
    ReconciliationRun,
)
from reconagent.services.actions import ActionRecommender
from reconagent.services.audit import AuditService
from reconagent.services.exceptions import DetectedException, ExceptionDetector
from reconagent.services.matching import MatchingEngine, components_json
from reconagent.services.policies import PolicyRetriever


class ReconciliationService:
    def __init__(self) -> None:
        self.matcher = MatchingEngine()
        self.detector = ExceptionDetector()
        self.policies = PolicyRetriever()
        self.actions = ActionRecommender()
        self.audit = AuditService()

    def create_run(self, session: Session) -> ReconciliationRun:
        run = ReconciliationRun(status="queued")
        session.add(run)
        session.flush()
        self.audit.append_event(
            session,
            entity_type="reconciliation_run",
            entity_id=run.id,
            actor_id="system",
            action="run_queued",
            payload={"status": run.status},
            run_id=run.id,
        )
        session.commit()
        return run

    def process_run(self, session: Session, run_id: str) -> ReconciliationRun:
        run = session.get(ReconciliationRun, run_id)
        if not run:
            raise ValueError(f"Unknown reconciliation run: {run_id}")

        try:
            run.status = "processing"
            self.audit.append_event(
                session,
                entity_type="reconciliation_run",
                entity_id=run.id,
                actor_id="system",
                action="run_processing",
                payload={"status": run.status},
                run_id=run.id,
            )

            invoices = list(session.scalars(select(Invoice)))
            payments = list(session.scalars(select(Payment)))
            ledger_entries = list(session.scalars(select(LedgerEntry)))
            matched_ledger_ids: set[str] = set()

            for invoice in invoices:
                match = self.matcher.find_best_match(invoice, payments, ledger_entries)
                if match.ledger_entry:
                    matched_ledger_ids.add(match.ledger_entry.id)
                session.add(
                    ReconciliationMatch(
                        run_id=run.id,
                        invoice_id=invoice.id,
                        payment_id=match.payment.id if match.payment else None,
                        ledger_entry_id=match.ledger_entry.id if match.ledger_entry else None,
                        score=match.score,
                        score_components=components_json(match.components),
                        status=match.status,
                    )
                )
                for detected in self.detector.detect_for_invoice(invoice, match, payments):
                    self.persist_exception(session, run.id, detected)

            for detected in self.detector.detect_unmatched_ledger_entries(
                matched_ledger_ids, ledger_entries
            ):
                self.persist_exception(session, run.id, detected)

            run.status = "completed"
            run.completed_at = datetime.now(UTC)
            self.audit.append_event(
                session,
                entity_type="reconciliation_run",
                entity_id=run.id,
                actor_id="system",
                action="run_completed",
                payload={"status": run.status},
                run_id=run.id,
            )
            session.commit()
            return run
        except Exception as exc:
            session.rollback()
            run = session.get(ReconciliationRun, run_id)
            if not run:
                raise
            run.status = "failed"
            run.error = str(exc)
            run.completed_at = datetime.now(UTC)
            self.audit.append_event(
                session,
                entity_type="reconciliation_run",
                entity_id=run.id,
                actor_id="system",
                action="run_failed",
                payload={"status": run.status, "error": str(exc)},
                run_id=run.id,
            )
            session.commit()
            raise

    def persist_exception(
        self, session: Session, run_id: str, detected: DetectedException
    ) -> ReconciliationException:
        citation = self.policies.retrieve(session, f"{detected.exception_type} {detected.explanation}")
        recommendation = self.actions.recommend(detected, citation)
        record = ReconciliationException(
            run_id=run_id,
            invoice_id=detected.invoice.id if detected.invoice else None,
            payment_id=detected.payment.id if detected.payment else None,
            ledger_entry_id=detected.ledger_entry.id if detected.ledger_entry else None,
            exception_type=detected.exception_type,
            severity=detected.severity,
            explanation=recommendation.explanation,
            proposed_action=recommendation.action,
            policy_citation=citation.text,
            requires_approval=recommendation.requires_approval,
            status="awaiting_approval" if recommendation.requires_approval else "auto_resolved",
        )
        session.add(record)
        session.flush()
        if recommendation.requires_approval:
            session.add(
                Approval(
                    exception_id=record.id,
                    proposed_action=recommendation.action,
                    status="pending",
                )
            )
        self.audit.append_event(
            session,
            entity_type="reconciliation_exception",
            entity_id=record.id,
            actor_id="system",
            action="exception_detected",
            payload={
                "exception_type": record.exception_type,
                "severity": record.severity,
                "proposed_action": record.proposed_action,
                "requires_approval": record.requires_approval,
            },
            run_id=run_id,
        )
        return record
