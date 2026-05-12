from __future__ import annotations

import re
import ast
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from reconagent.models import PolicyChunk
from reconagent.services.embeddings import cosine_similarity, local_text_embedding


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
                vector_score(query_vector, chunk.embedding_json),
                len(query_terms & token_set(chunk.chunk_text)),
            ),
        )
        score = round(vector_score(query_vector, best.embedding_json) * 100)
        return PolicyCitation(best.policy_id, best.id, best.chunk_text, score)


def token_set(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9_]+", text.lower()) if len(token) > 2}


def vector_score(query_vector: list[float], embedding_json: str | None) -> float:
    if not embedding_json:
        return 0.0
    try:
        vector = [float(value) for value in ast.literal_eval(embedding_json)]
    except (ValueError, SyntaxError):
        return 0.0
    return cosine_similarity(query_vector, vector)
