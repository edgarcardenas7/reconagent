from __future__ import annotations

import json
from dataclasses import dataclass

from reconagent.config import get_settings
from reconagent.services.exceptions import DetectedException
from reconagent.services.policies import PolicyCitation

ACTION_APPROVE = "approve"
ACTION_HOLD_FOR_REVIEW = "hold_for_review"
ACTION_REQUEST_DOCUMENT = "request_document"
ACTION_SEND_FOLLOW_UP = "send_follow_up"
ACTION_ESCALATE_TO_CONTROLLER = "escalate_to_controller"

ALLOWED_ACTIONS = {
    ACTION_APPROVE,
    ACTION_HOLD_FOR_REVIEW,
    ACTION_REQUEST_DOCUMENT,
    ACTION_SEND_FOLLOW_UP,
    ACTION_ESCALATE_TO_CONTROLLER,
}

ACTIONS_REQUIRING_APPROVAL = {
    ACTION_APPROVE,
    ACTION_HOLD_FOR_REVIEW,
    ACTION_REQUEST_DOCUMENT,
    ACTION_ESCALATE_TO_CONTROLLER,
}


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
            "duplicate_payment": ACTION_HOLD_FOR_REVIEW,
            "amount_mismatch": ACTION_HOLD_FOR_REVIEW,
            "missing_po": ACTION_REQUEST_DOCUMENT,
            "changed_bank_account": ACTION_ESCALATE_TO_CONTROLLER,
            "overdue_invoice": ACTION_SEND_FOLLOW_UP,
            "unmatched_invoice": ACTION_HOLD_FOR_REVIEW,
            "unmatched_ledger_entry": ACTION_HOLD_FOR_REVIEW,
        }
        action = mapping.get(exception.exception_type, ACTION_HOLD_FOR_REVIEW)
        explanation = (
            f"{exception.explanation} Relevant policy context: {citation.text[:350]}"
        )
        return ProposedAction(
            action,
            explanation,
            requires_approval=action in ACTIONS_REQUIRING_APPROVAL,
        )

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
            return coerce_llm_recommendation(data, fallback)
        except Exception:
            return fallback


def coerce_llm_recommendation(data: dict, fallback: ProposedAction) -> ProposedAction:
    action = data.get("action")
    if action not in ALLOWED_ACTIONS:
        return fallback

    model_requires_approval = bool(data.get("requires_approval", True))
    action_requires_approval = action in ACTIONS_REQUIRING_APPROVAL
    requires_approval = (
        fallback.requires_approval
        or action_requires_approval
        or model_requires_approval
    )
    return ProposedAction(
        action,
        data.get("explanation", fallback.explanation),
        requires_approval,
    )
