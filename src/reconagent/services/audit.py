from __future__ import annotations

import hashlib
import json

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from reconagent.models import AuditEvent

GENESIS_HASH = "0" * 64


class AuditService:
    def append_event(
        self,
        session: Session,
        *,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        action: str,
        payload: dict,
        run_id: str | None = None,
    ) -> AuditEvent:
        previous_hash = self.latest_hash(session)
        payload_json = canonical_json(payload)
        event_hash = compute_event_hash(
            previous_hash=previous_hash,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            action=action,
            payload_json=payload_json,
        )
        event = AuditEvent(
            run_id=run_id,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            action=action,
            payload_json=payload_json,
            previous_hash=previous_hash,
            event_hash=event_hash,
        )
        session.add(event)
        session.flush()
        return event

    @staticmethod
    def latest_hash(session: Session) -> str:
        event = session.scalar(select(AuditEvent).order_by(desc(AuditEvent.created_at), desc(AuditEvent.id)))
        return event.event_hash if event else GENESIS_HASH


def canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def compute_event_hash(
    *,
    previous_hash: str,
    entity_type: str,
    entity_id: str,
    actor_id: str,
    action: str,
    payload_json: str,
) -> str:
    material = "|".join([previous_hash, entity_type, entity_id, actor_id, action, payload_json])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()
