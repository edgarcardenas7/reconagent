DEMO_USERS = {
    "analyst": {"role": "finance_analyst"},
    "controller": {"role": "controller"},
    "cfo": {"role": "cfo"},
}

HIGH_RISK_ACTIONS = {"hold_for_review", "escalate_to_controller"}


def can_decide(actor_id: str, proposed_action: str) -> bool:
    user = DEMO_USERS.get(actor_id)
    if not user:
        return False
    role = user["role"]
    if proposed_action == "escalate_to_controller":
        return role in {"controller", "cfo"}
    if proposed_action in HIGH_RISK_ACTIONS:
        return role in {"controller", "cfo"}
    return role in {"finance_analyst", "controller", "cfo"}
