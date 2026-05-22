from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from reconagent.domain.normalization import (
    normalize_invoice_row,
    normalize_ledger_row,
    normalize_payment_row,
    read_csv_bytes,
)
from reconagent.models import FinancePolicy, Invoice, LedgerEntry, Payment, PolicyChunk, Vendor
from reconagent.services.embeddings import local_text_embedding


def get_or_create_vendor(session: Session, name: str, normalized_name: str) -> Vendor:
    vendor = session.scalar(select(Vendor).where(Vendor.normalized_name == normalized_name))
    if vendor:
        return vendor

    vendor = Vendor(name=name, normalized_name=normalized_name)
    session.add(vendor)
    session.flush()
    return vendor


def source_hash_exists(
    session: Session,
    model: type[Invoice] | type[Payment] | type[LedgerEntry],
    source_hash: str,
) -> bool:
    return session.scalar(select(model.id).where(model.source_hash == source_hash)) is not None


def import_invoices(session: Session, content: bytes) -> list[str]:
    ids: list[str] = []
    try:
        for row in read_csv_bytes(content):
            data = normalize_invoice_row(row)
            if source_hash_exists(session, Invoice, data["source_hash"]):
                continue
            vendor = get_or_create_vendor(
                session, data.pop("vendor_name"), data.pop("normalized_vendor_name")
            )
            invoice = Invoice(vendor_id=vendor.id, vendor_name=vendor.name, **data)
            session.add(invoice)
            session.flush()
            ids.append(invoice.id)
        session.commit()
        return ids
    except Exception:
        session.rollback()
        raise


def import_payments(session: Session, content: bytes) -> list[str]:
    ids: list[str] = []
    try:
        for row in read_csv_bytes(content):
            data = normalize_payment_row(row)
            if source_hash_exists(session, Payment, data["source_hash"]):
                continue
            vendor = get_or_create_vendor(
                session, data.pop("vendor_name"), data.pop("normalized_vendor_name")
            )
            payment = Payment(vendor_id=vendor.id, vendor_name=vendor.name, **data)
            session.add(payment)
            session.flush()
            ids.append(payment.id)
        session.commit()
        return ids
    except Exception:
        session.rollback()
        raise


def import_ledger_entries(session: Session, content: bytes) -> list[str]:
    ids: list[str] = []
    try:
        for row in read_csv_bytes(content):
            data = normalize_ledger_row(row)
            if source_hash_exists(session, LedgerEntry, data["source_hash"]):
                continue
            vendor = get_or_create_vendor(
                session, data.pop("vendor_name"), data.pop("normalized_vendor_name")
            )
            entry = LedgerEntry(vendor_id=vendor.id, vendor_name=vendor.name, **data)
            session.add(entry)
            session.flush()
            ids.append(entry.id)
        session.commit()
        return ids
    except Exception:
        session.rollback()
        raise


def import_policies(session: Session, content: bytes) -> list[str]:
    ids: list[str] = []
    try:
        for row in read_csv_bytes(content):
            policy = FinancePolicy(
                title=row["title"].strip(),
                body=row["body"].strip(),
                risk_level=row.get("risk_level", "medium").strip() or "medium",
            )
            session.add(policy)
            session.flush()
            for chunk in chunk_policy(policy.body):
                session.add(
                    PolicyChunk(
                        policy_id=policy.id,
                        chunk_text=chunk,
                        embedding_json=str(local_text_embedding(chunk)),
                    )
                )
            ids.append(policy.id)
        session.commit()
        return ids
    except Exception:
        session.rollback()
        raise


def chunk_policy(text: str, max_chars: int = 700) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 1 > max_chars and current:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n{paragraph}".strip()
    if current:
        chunks.append(current)
    return chunks or [text]
