from reconagent.services.actions import ProposedAction, coerce_llm_recommendation


def test_llm_recommendation_cannot_remove_required_human_approval():
    fallback = ProposedAction(
        action="escalate_to_controller",
        explanation="Changed bank account requires controller review.",
        requires_approval=True,
    )

    recommendation = coerce_llm_recommendation(
        {
            "action": "send_follow_up",
            "explanation": "Just ask the vendor to confirm later.",
            "requires_approval": False,
        },
        fallback,
    )

    assert recommendation.action == "send_follow_up"
    assert recommendation.requires_approval is True


def test_llm_recommendation_returns_fallback_for_unknown_action():
    fallback = ProposedAction(
        action="hold_for_review",
        explanation="Unknown exception should be reviewed.",
        requires_approval=True,
    )

    recommendation = coerce_llm_recommendation(
        {
            "action": "wire_money_now",
            "explanation": "Unsafe invented action.",
            "requires_approval": False,
        },
        fallback,
    )

    assert recommendation == fallback


def test_llm_recommendation_can_keep_low_risk_follow_up_without_approval():
    fallback = ProposedAction(
        action="send_follow_up",
        explanation="Overdue invoice needs a reminder.",
        requires_approval=False,
    )

    recommendation = coerce_llm_recommendation(
        {
            "action": "send_follow_up",
            "explanation": "Send a polite follow-up.",
            "requires_approval": False,
        },
        fallback,
    )

    assert recommendation.action == "send_follow_up"
    assert recommendation.requires_approval is False
