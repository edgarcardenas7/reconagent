from __future__ import annotations

import ast
import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from reconagent.models import PolicyChunk
from reconagent.services.embeddings import cosine_similarity, local_text_embedding

MIN_TOKEN_LENGTH = 3
EXCEPTION_POLICY_TERMS = {
    "duplicate_payment": (
        "duplicate payment duplicate payments seven days vendor invoice number payment reference "
        "bank account hold review"
    ),
    "amount_mismatch": (
        "amount mismatch invoice payment difference tolerance hold review"
    ),
    "missing_po": (
        "missing po missing purchase order invoice without purchase order document request"
    ),
    "changed_bank_account": (
        "changed bank account changed vendor bank accounts bank account mismatch controller "
        "escalation high risk"
    ),
    "overdue_invoice": (
        "overdue invoice late payment follow up unpaid invoice"
    ),
    "unmatched_invoice": (
        "unmatched invoice no payment match hold review"
    ),
    "unmatched_ledger_entry": (
        "unmatched ledger entry accounting consistency reconciled invoice ledger"
    ),
}


@dataclass(frozen=True)
class PolicyCitation:
    policy_id: str | None
    chunk_id: str | None
    text: str
    score: int


class PolicyRetriever:
    def retrieve(self, session: Session, query: str) -> PolicyCitation:
        chunks = list(session.scalars(select(PolicyChunk)))
        if not chunks:
            return PolicyCitation(None, None, "No policy text imported; fallback rules applied.", 0)

        query_terms = token_set(query)
        query_vector = local_text_embedding(query)
        best = max(
            chunks,
            key=lambda chunk: (
                len(query_terms & token_set(chunk.chunk_text)),
                vector_score(query_vector, chunk.embedding_json),
            ),
        )
        score = round(vector_score(query_vector, best.embedding_json) * 100)
        return PolicyCitation(best.policy_id, best.id, best.chunk_text, score)


def token_set(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", text.lower())
        if len(token) >= MIN_TOKEN_LENGTH
    }


def policy_query_for_exception(exception_type: str, explanation: str) -> str:
    domain_terms = EXCEPTION_POLICY_TERMS.get(exception_type, exception_type.replace("_", " "))
    return f"{domain_terms} {explanation}"


def vector_score(query_vector: list[float], embedding_json: str | None) -> float:
    if not embedding_json:
        return 0.0
    try:
        vector = [float(value) for value in ast.literal_eval(embedding_json)]
    except (ValueError, SyntaxError):
        return 0.0
    return cosine_similarity(query_vector, vector)
