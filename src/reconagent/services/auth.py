ROLE_FINANCE_ANALYST = "finance_analyst"
ROLE_CONTROLLER = "controller"
ROLE_CFO = "cfo"

ACTION_APPROVE = "approve"
ACTION_HOLD_FOR_REVIEW = "hold_for_review"
ACTION_REQUEST_DOCUMENT = "request_document"
ACTION_SEND_FOLLOW_UP = "send_follow_up"
ACTION_ESCALATE_TO_CONTROLLER = "escalate_to_controller"

DEMO_USERS = {
    "analyst": {"role": ROLE_FINANCE_ANALYST},
    "controller": {"role": ROLE_CONTROLLER},
    "cfo": {"role": ROLE_CFO},
}

ALLOWED_ROLES_BY_ACTION = {
    ACTION_APPROVE: {ROLE_FINANCE_ANALYST, ROLE_CONTROLLER, ROLE_CFO},
    ACTION_HOLD_FOR_REVIEW: {ROLE_CONTROLLER, ROLE_CFO},
    ACTION_REQUEST_DOCUMENT: {ROLE_FINANCE_ANALYST, ROLE_CONTROLLER, ROLE_CFO},
    ACTION_SEND_FOLLOW_UP: {ROLE_FINANCE_ANALYST, ROLE_CONTROLLER, ROLE_CFO},
    ACTION_ESCALATE_TO_CONTROLLER: {ROLE_CONTROLLER, ROLE_CFO},
}


def can_decide(actor_id: str, proposed_action: str) -> bool:
    user = DEMO_USERS.get(actor_id)
    if not user:
        return False
    role = user["role"]
    allowed_roles = ALLOWED_ROLES_BY_ACTION.get(proposed_action)
    if not allowed_roles:
        return False
    return role in allowed_roles
