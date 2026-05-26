from __future__ import annotations

import json
from dataclasses import dataclass
from difflib import SequenceMatcher

from reconagent.domain.normalization import normalize_reference
from reconagent.models import Invoice, LedgerEntry, Payment


MATCH_THRESHOLD = 70
VENDOR_MATCH_POINTS = 35
EXACT_AMOUNT_POINTS = 30
SMALL_AMOUNT_MISMATCH_POINTS = 20
MODERATE_AMOUNT_MISMATCH_POINTS = 10
SMALL_AMOUNT_MISMATCH_RATIO = 0.02
MODERATE_AMOUNT_MISMATCH_RATIO = 0.05
ON_TIME_PAYMENT_POINTS = 20
NEAR_DATE_PAYMENT_POINTS = 15
DISTANT_DATE_PAYMENT_POINTS = 8
EARLY_PAYMENT_WINDOW_DAYS = -3
SLIGHTLY_EARLY_PAYMENT_WINDOW_DAYS = -7
ON_TIME_PAYMENT_WINDOW_DAYS = 7
NEAR_DATE_PAYMENT_WINDOW_DAYS = 30
DISTANT_DATE_PAYMENT_WINDOW_DAYS = 90
REFERENCE_MATCH_POINTS = 10
LEDGER_LOOKUP_WINDOW_DAYS = 14
LEDGER_CONSISTENCY_POINTS = 5


@dataclass(frozen=True)
class MatchResult:
    payment: Payment | None
    ledger_entry: LedgerEntry | None
    score: int
    components: dict[str, int]
    status: str


class MatchingEngine:
    def find_best_match(
        self,
        invoice: Invoice,
        payments: list[Payment],
        ledger_entries: list[LedgerEntry],
    ) -> MatchResult:
        same_currency_payments = [
            payment for payment in payments if payment.currency == invoice.currency
        ]
        candidates = [
            self.score_invoice_payment(invoice, payment) for payment in same_currency_payments
        ]
        best_payment, components = max(candidates, key=lambda item: sum(item[1].values()), default=(None, {}))
        ledger_entry = self.find_ledger_entry(invoice, ledger_entries)

        if ledger_entry:
            components["ledger_consistency"] = LEDGER_CONSISTENCY_POINTS
        elif components:
            components["ledger_consistency"] = 0

        score = sum(components.values()) if components else 0
        status = "matched" if score >= MATCH_THRESHOLD else "unmatched"
        matched_payment = best_payment if status == "matched" else None
        matched_ledger_entry = ledger_entry if status == "matched" else None
        return MatchResult(matched_payment, matched_ledger_entry, score, components, status)

    def score_invoice_payment(
        self, invoice: Invoice, payment: Payment
    ) -> tuple[Payment, dict[str, int]]:
        components = {
            "vendor_match": VENDOR_MATCH_POINTS if invoice.vendor_id == payment.vendor_id else 0,
            "amount_match": self.amount_score(invoice.amount_cents, payment.amount_cents),
            "date_window": self.date_score((payment.payment_date - invoice.invoice_date).days),
            "reference_similarity": self.reference_score(invoice.invoice_number, payment.reference),
        }
        return payment, components

    def find_ledger_entry(
        self, invoice: Invoice, ledger_entries: list[LedgerEntry]
    ) -> LedgerEntry | None:
        for entry in ledger_entries:
            days = abs((entry.entry_date - invoice.invoice_date).days)
            same_currency = entry.currency == invoice.currency
            same_vendor = entry.vendor_id == invoice.vendor_id
            same_amount = entry.amount_cents == invoice.amount_cents
            ref_match = normalize_reference(invoice.invoice_number) in normalize_reference(entry.reference)
            if same_currency and same_vendor and same_amount and (days <= LEDGER_LOOKUP_WINDOW_DAYS or ref_match):
                return entry
        return None

    @staticmethod
    def amount_score(invoice_cents: int, payment_cents: int) -> int:
        if invoice_cents == payment_cents:
            return EXACT_AMOUNT_POINTS
        diff_ratio = abs(invoice_cents - payment_cents) / max(invoice_cents, 1)
        if diff_ratio <= SMALL_AMOUNT_MISMATCH_RATIO:
            return SMALL_AMOUNT_MISMATCH_POINTS
        if diff_ratio <= MODERATE_AMOUNT_MISMATCH_RATIO:
            return MODERATE_AMOUNT_MISMATCH_POINTS
        return 0

    @staticmethod
    def date_score(delta_days: int) -> int:
        if 0 <= delta_days <= ON_TIME_PAYMENT_WINDOW_DAYS:
            return ON_TIME_PAYMENT_POINTS
        if EARLY_PAYMENT_WINDOW_DAYS <= delta_days <= NEAR_DATE_PAYMENT_WINDOW_DAYS:
            return NEAR_DATE_PAYMENT_POINTS
        if SLIGHTLY_EARLY_PAYMENT_WINDOW_DAYS <= delta_days <= DISTANT_DATE_PAYMENT_WINDOW_DAYS:
            return DISTANT_DATE_PAYMENT_POINTS
        return 0

    @staticmethod
    def reference_score(invoice_number: str, payment_reference: str) -> int:
        invoice_ref = normalize_reference(invoice_number)
        payment_ref = normalize_reference(payment_reference)
        if invoice_ref and invoice_ref in payment_ref:
            return REFERENCE_MATCH_POINTS
        return round(SequenceMatcher(None, invoice_ref, payment_ref).ratio() * REFERENCE_MATCH_POINTS)


def components_json(components: dict[str, int]) -> str:
    return json.dumps(components, sort_keys=True)
