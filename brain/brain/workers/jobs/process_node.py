"""Job stub Phase 1: registra el evento. Phase 2 añade chunk+embed+KG."""
from __future__ import annotations

from datetime import datetime, timezone

from brain.settings import get_settings
from brain.storage.events import EventLog


def process_node(node_id: str) -> dict:
    settings = get_settings()
    events = EventLog(f"{settings.events_path}/events.db")
    events.append(
        event_type="process",
        user_id=settings.user_id,
        source="worker",
        node_id=node_id,
        provenance_rule="brain.workers.process_node.v1",
        payload={
            "phase": 1,
            "note": "stub — pipeline real en Phase 2 (chunk + embed + KG)",
            "processed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    )
    return {"node_id": node_id, "status": "noop", "phase": 1}
