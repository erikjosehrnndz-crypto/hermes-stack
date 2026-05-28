"""Job: extrae hechos clave de una conversación y los guarda como memorias."""
from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

_LITELLM_URL = "http://litellm:4000"
_MODEL = "gemini-flash"

_EXTRACT_PROMPT = """Extrae los hechos clave, decisiones, preferencias y aprendizajes de esta conversación.
Devuelve SOLO un array JSON de strings. Cada string es un hecho concreto, independiente y útil para recordar.
Máximo 8 hechos. Ejemplo:
["Erik prefiere commits pequeños por tarea", "El stack usa LiteLLM como proxy LLM", "Se decidió usar trafilatura para extracción de URLs"]

Conversación:
{text}

Array JSON:"""


def extract_memories(text: str, node_id: str | None = None) -> dict:
    """Extrae hechos de una conversación y los almacena como memorias individuales.

    Usa gemini-flash para extraer hechos. Cada hecho se embede y guarda en
    la tabla `memories` de LanceDB.
    """
    import json as _json

    import httpx

    from brain.pipeline.embed import embed_query
    from brain.settings import get_settings
    from brain.storage.events import EventLog
    from brain.storage.lance import LanceStore

    settings = get_settings()
    lance = LanceStore(settings.lance_path, dim=settings.embed_dim)
    events = EventLog(f"{settings.events_path}/events.db")
    api_key = os.environ.get("LITELLM_MASTER_KEY", "")

    # Truncar si es muy largo
    text_input = text[:6000]

    facts: list[str] = []
    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{_LITELLM_URL}/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": _MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": _EXTRACT_PROMPT.format(text=text_input),
                        }
                    ],
                    "max_tokens": 600,
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"].strip()

            # Extraer el array JSON de la respuesta (puede venir con texto alrededor)
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start >= 0 and end > start:
                facts = _json.loads(raw[start:end])
                facts = [f for f in facts if isinstance(f, str) and len(f.strip()) > 5]
    except Exception as e:
        log.warning("extract_memories: LLM call failed: %s", e)
        return {"status": "error", "error": str(e), "node_id": node_id}

    if not facts:
        return {"status": "ok", "n_facts": 0, "node_id": node_id}

    # Guardar cada hecho como memoria
    from datetime import datetime, timezone
    import uuid

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    stored = 0
    for fact in facts:
        try:
            vec = embed_query(fact, model_name=settings.embed_model)
            memory_id = f"mem-{uuid.uuid4().hex[:12]}"
            lance.remember(
                fact,
                vector=vec,
                user_id=settings.user_id,
                memory_id=memory_id,
                source="extract_memories",
                created_at=now_iso,
            )
            stored += 1
        except Exception as e:
            log.warning("extract_memories: failed to store fact: %s", e)

    events.append(
        event_type="extract_memories",
        user_id=settings.user_id,
        source="worker",
        node_id=node_id or "batch",
        payload={"n_facts": len(facts), "n_stored": stored},
    )

    return {"status": "ok", "n_facts": len(facts), "n_stored": stored, "node_id": node_id}
