from __future__ import annotations

import json
from dataclasses import dataclass

from reconagent.config import get_settings
from reconagent.services.exceptions import DetectedException
from reconagent.services.policies import PolicyCitation


@dataclass(frozen=True)
class ProposedAction:
    action: str
    explanation: str
    requires_approval: bool


class ActionRecommender:
    def recommend(self, exception: DetectedException, citation: PolicyCitation) -> ProposedAction:
        fallback = self.fallback_recommendation(exception, citation)
        if not get_settings().openai_api_key:
            return fallback
        return self.llm_recommendation(exception, citation, fallback)

    def fallback_recommendation(
        self, exception: DetectedException, citation: PolicyCitation
    ) -> ProposedAction:
        mapping = {
            "duplicate_payment": "hold_for_review",
            "amount_mismatch": "hold_for_review",
            "missing_po": "request_document",
            "changed_bank_account": "escalate_to_controller",
            "overdue_invoice": "send_follow_up",
            "unmatched_invoice": "hold_for_review",
            "unmatched_ledger_entry": "hold_for_review",
        }
        action = mapping.get(exception.exception_type, "hold_for_review")
        explanation = (
            f"{exception.explanation} Relevant policy context: {citation.text[:350]}"
        )
        return ProposedAction(action, explanation, requires_approval=action != "send_follow_up")

    def llm_recommendation(
        self,
        exception: DetectedException,
        citation: PolicyCitation,
        fallback: ProposedAction,
    ) -> ProposedAction:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=get_settings().openai_api_key)
            response = client.responses.create(
                model=get_settings().openai_model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are a finance operations control assistant. "
                            "Return strict JSON with action, explanation, requires_approval. "
                            "Allowed actions: approve, hold_for_review, request_document, "
                            "send_follow_up, escalate_to_controller."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Exception type: {exception.exception_type}\n"
                            f"Severity: {exception.severity}\n"
                            f"Finding: {exception.explanation}\n"
                            f"Policy: {citation.text}"
                        ),
                    },
                ],
            )
            raw = response.output_text
            data = json.loads(raw)
            if data["action"] not in {
                "approve",
                "hold_for_review",
                "request_document",
                "send_follow_up",
                "escalate_to_controller",
            }:
                return fallback
            return ProposedAction(
                data["action"],
                data.get("explanation", fallback.explanation),
                bool(data.get("requires_approval", True)),
            )
        except Exception:
            return fallback
