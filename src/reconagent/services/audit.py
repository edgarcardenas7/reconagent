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

    def verify_chain(self, session: Session) -> bool:
        events = list(session.scalars(select(AuditEvent)))
        if not events:
            return True

        visited_ids: set[str] = set()
        expected_previous_hash = GENESIS_HASH
        while len(visited_ids) < len(events):
            next_events = [
                event
                for event in events
                if event.previous_hash == expected_previous_hash and event.id not in visited_ids
            ]
            if len(next_events) != 1:
                return False

            event = next_events[0]
            expected_event_hash = compute_event_hash(
                previous_hash=event.previous_hash,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                actor_id=event.actor_id,
                action=event.action,
                payload_json=event.payload_json,
            )
            if event.event_hash != expected_event_hash:
                return False

            visited_ids.add(event.id)
            expected_previous_hash = event.event_hash

        return True


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
