from reconagent.services.audit import AuditService


def test_audit_chain_verification_detects_tampered_event(db_session):
    audit = AuditService()

    first = audit.append_event(
        db_session,
        entity_type="approval",
        entity_id="approval-1",
        actor_id="controller",
        action="approval_approved",
        payload={"decision": "approved"},
    )
    audit.append_event(
        db_session,
        entity_type="approval",
        entity_id="approval-2",
        actor_id="controller",
        action="approval_rejected",
        payload={"decision": "rejected"},
    )

    assert audit.verify_chain(db_session)

    first.payload_json = '{"decision":"rejected"}'
    db_session.flush()

    assert not audit.verify_chain(db_session)
