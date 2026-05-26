from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from reconagent.domain.normalization import normalize_reference
from reconagent.models import Invoice, LedgerEntry, Payment
from reconagent.services.matching import MatchResult


SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"

EXCEPTION_UNMATCHED_INVOICE = "unmatched_invoice"
EXCEPTION_MISSING_PO = "missing_po"
EXCEPTION_AMOUNT_MISMATCH = "amount_mismatch"
EXCEPTION_CHANGED_BANK_ACCOUNT = "changed_bank_account"
EXCEPTION_OVERDUE_INVOICE = "overdue_invoice"
EXCEPTION_DUPLICATE_PAYMENT = "duplicate_payment"
EXCEPTION_UNMATCHED_LEDGER_ENTRY = "unmatched_ledger_entry"

DUPLICATE_PAYMENT_WINDOW_DAYS = 7


@dataclass(frozen=True)
class DetectedException:
    exception_type: str
    severity: str
    explanation: str
    invoice: Invoice | None = None
    payment: Payment | None = None
    ledger_entry: LedgerEntry | None = None


class ExceptionDetector:
    def detect_for_invoice(
        self,
        invoice: Invoice,
        match: MatchResult,
        payments: list[Payment],
        today: date | None = None,
    ) -> list[DetectedException]:
        today = today or date.today()
        exceptions: list[DetectedException] = []

        if match.status == "unmatched":
            exceptions.append(
                DetectedException(
                    EXCEPTION_UNMATCHED_INVOICE,
                    SEVERITY_MEDIUM,
                    f"Invoice {invoice.invoice_number} does not have a confident payment match.",
                    invoice=invoice,
                )
            )

        if not invoice.po_number:
            exceptions.append(
                DetectedException(
                    EXCEPTION_MISSING_PO,
                    SEVERITY_MEDIUM,
                    f"Invoice {invoice.invoice_number} has no purchase order number.",
                    invoice=invoice,
                    payment=match.payment,
                )
            )

        if match.payment and invoice.amount_cents != match.payment.amount_cents:
            exceptions.append(
                DetectedException(
                    EXCEPTION_AMOUNT_MISMATCH,
                    SEVERITY_HIGH,
                    f"Invoice {invoice.invoice_number} amount does not equal matched payment amount.",
                    invoice=invoice,
                    payment=match.payment,
                )
            )

        if match.payment and invoice.bank_account and invoice.bank_account != match.payment.bank_account:
            exceptions.append(
                DetectedException(
                    EXCEPTION_CHANGED_BANK_ACCOUNT,
                    SEVERITY_HIGH,
                    f"Vendor bank account differs between invoice {invoice.invoice_number} and payment.",
                    invoice=invoice,
                    payment=match.payment,
                )
            )

        if invoice.due_date < today and not match.payment:
            exceptions.append(
                DetectedException(
                    EXCEPTION_OVERDUE_INVOICE,
                    SEVERITY_MEDIUM,
                    f"Invoice {invoice.invoice_number} is overdue and no payment was matched.",
                    invoice=invoice,
                )
            )

        exceptions.extend(self.detect_duplicate_payments(invoice, payments))
        return dedupe_exceptions(exceptions)

    def detect_duplicate_payments(
        self, invoice: Invoice, payments: list[Payment]
    ) -> list[DetectedException]:
        related = [
            p
            for p in payments
            if p.vendor_id == invoice.vendor_id
            and p.amount_cents == invoice.amount_cents
            and p.currency == invoice.currency
        ]
        duplicates: list[DetectedException] = []
        for index, payment in enumerate(related):
            for other in related[index + 1 :]:
                if (
                    abs((payment.payment_date - other.payment_date).days)
                    <= DUPLICATE_PAYMENT_WINDOW_DAYS
                    and references_are_compatible(payment.reference, other.reference)
                ):
                    duplicates.append(
                        DetectedException(
                            EXCEPTION_DUPLICATE_PAYMENT,
                            SEVERITY_HIGH,
                            f"Vendor {invoice.vendor_name} has duplicate-sized payments within "
                            f"{DUPLICATE_PAYMENT_WINDOW_DAYS} days.",
                            invoice=invoice,
                            payment=other,
                        )
                    )
        return duplicates

    def detect_unmatched_ledger_entries(
        self, matched_ledger_ids: set[str], ledger_entries: list[LedgerEntry]
    ) -> list[DetectedException]:
        return [
            DetectedException(
                EXCEPTION_UNMATCHED_LEDGER_ENTRY,
                SEVERITY_MEDIUM,
                f"Ledger entry {entry.reference} was not tied to a reconciled invoice.",
                ledger_entry=entry,
            )
            for entry in ledger_entries
            if entry.id not in matched_ledger_ids
        ]


def dedupe_exceptions(exceptions: list[DetectedException]) -> list[DetectedException]:
    seen: set[tuple[str, str | None, str | None, str | None]] = set()
    output: list[DetectedException] = []
    for exc in exceptions:
        key = (
            exc.exception_type,
            exc.invoice.id if exc.invoice else None,
            exc.payment.id if exc.payment else None,
            exc.ledger_entry.id if exc.ledger_entry else None,
        )
        if key not in seen:
            output.append(exc)
            seen.add(key)
    return output


def references_are_compatible(first_reference: str, second_reference: str) -> bool:
    first = normalize_reference(first_reference)
    second = normalize_reference(second_reference)
    if not first or not second:
        return True
    if first == second:
        return True
    return token_sequence_contains(reference_tokens(first_reference), reference_tokens(second_reference))


def reference_tokens(reference: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", reference.lower())


def token_sequence_contains(first_tokens: list[str], second_tokens: list[str]) -> bool:
    shorter, longer = sorted((first_tokens, second_tokens), key=len)
    if not shorter:
        return False
    window_size = len(shorter)
    return any(
        longer[index : index + window_size] == shorter
        for index in range(len(longer) - window_size + 1)
    )
