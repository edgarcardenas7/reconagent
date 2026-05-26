from reconagent.services.auth import can_decide


def test_finance_analyst_can_decide_low_risk_actions_only():
    assert can_decide("analyst", "request_document")
    assert can_decide("analyst", "send_follow_up")
    assert not can_decide("analyst", "hold_for_review")
    assert not can_decide("analyst", "escalate_to_controller")


def test_controller_can_decide_high_risk_actions():
    assert can_decide("controller", "hold_for_review")
    assert can_decide("controller", "escalate_to_controller")


def test_unknown_approval_action_cannot_be_decided():
    assert not can_decide("analyst", "wire_money_now")


def test_unknown_actor_cannot_decide_known_action():
    assert not can_decide("unknown-user", "request_document")
