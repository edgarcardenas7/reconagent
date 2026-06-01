"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "finance_policies",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "reconciliation_runs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime()),
        sa.Column("error", sa.Text()),
    )
    op.create_table(
        "invoices",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("vendor_id", sa.String(), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("invoice_number", sa.String(length=100), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("po_number", sa.String(length=100)),
        sa.Column("bank_account", sa.String(length=64)),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("vendor_id", sa.String(), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("bank_account", sa.String(length=64), nullable=False),
        sa.Column("reference", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("vendor_id", sa.String(), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("account_code", sa.String(length=64), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("reference", sa.String(length=255), nullable=False),
        sa.Column("source_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "policy_chunks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("policy_id", sa.String(), sa.ForeignKey("finance_policies.id"), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("embedding_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "reconciliation_matches",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("reconciliation_runs.id"), nullable=False),
        sa.Column("invoice_id", sa.String(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("payment_id", sa.String(), sa.ForeignKey("payments.id")),
        sa.Column("ledger_entry_id", sa.String(), sa.ForeignKey("ledger_entries.id")),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("score_components", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "reconciliation_exceptions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("reconciliation_runs.id"), nullable=False),
        sa.Column("invoice_id", sa.String(), sa.ForeignKey("invoices.id")),
        sa.Column("payment_id", sa.String(), sa.ForeignKey("payments.id")),
        sa.Column("ledger_entry_id", sa.String(), sa.ForeignKey("ledger_entries.id")),
        sa.Column("exception_type", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("proposed_action", sa.String(length=64), nullable=False),
        sa.Column("policy_citation", sa.Text(), nullable=False),
        sa.Column("requires_approval", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "approvals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("exception_id", sa.String(), sa.ForeignKey("reconciliation_exceptions.id"), nullable=False),
        sa.Column("proposed_action", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("decision", sa.String(length=40)),
        sa.Column("decided_by", sa.String(length=100)),
        sa.Column("decided_at", sa.DateTime()),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("reconciliation_runs.id")),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("actor_id", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("previous_hash", sa.String(length=64), nullable=False),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "audit_events",
        "approvals",
        "reconciliation_exceptions",
        "reconciliation_matches",
        "policy_chunks",
        "ledger_entries",
        "payments",
        "invoices",
        "reconciliation_runs",
        "finance_policies",
        "vendors",
    ]:
        op.drop_table(table)
