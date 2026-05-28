"""Phase 2 worker: lee el nodo del vault → chunk → embed → LanceDB upsert.

Idempotente: borra cualquier registro previo del `node_id` antes de insertar.
Eventos:
  - `process_start` (id, len_body, n_chunks_planned)
  - `process_done`  (id, n_chunks, dim, ms)
  - `process_error` (id, error)
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import frontmatter

from brain.pipeline.chunk import chunk_text
from brain.pipeline.embed import embed_texts, embed_dim
from brain.pipeline.extract_mentions import extract_wikilinks
from brain.settings import get_settings
from brain.storage.events import EventLog
from brain.storage.graph import KuzuGraph
from brain.storage.lance import LanceStore
from brain.storage.vault import Vault


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _find_node_path(vault_root: Path, node_id: str) -> Path | None:
    if node_id.startswith("jn-"):
        date = node_id[3:]
        p = vault_root / "journal" / f"{date}.md"
        return p if p.exists() else None
    for sub in ("notes", "memories", "sources"):
        p = vault_root / sub / f"{node_id}.md"
        if p.exists():
            return p
    # Fallback global por si el layout crece.
    for p in vault_root.rglob(f"{node_id}.md"):
        return p
    return None


def process_node(node_id: str) -> dict:
    settings = get_settings()
    events = EventLog(f"{settings.events_path}/events.db")
    vault_root = Path(settings.vault_path)

    path = _find_node_path(vault_root, node_id)
    if path is None:
        events.append(
            event_type="process_error",
            user_id=settings.user_id,
            source="worker",
            node_id=node_id,
            provenance_rule="brain.workers.process_node.v2",
            payload={"error": "node_not_found"},
        )
        return {"node_id": node_id, "status": "error", "error": "node_not_found"}

    try:
        post = frontmatter.load(path)
        meta = dict(post.metadata)
        body = (post.content or "").strip()
    except Exception as e:
        events.append(
            event_type="process_error",
            user_id=settings.user_id,
            source="worker",
            node_id=node_id,
            provenance_rule="brain.workers.process_node.v2",
            payload={"error": f"frontmatter_parse: {e}"},
        )
        return {"node_id": node_id, "status": "error", "error": str(e)}

    chunks = chunk_text(
        body,
        max_tokens=settings.chunk_max_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
    )

    events.append(
        event_type="process_start",
        user_id=settings.user_id,
        source="worker",
        node_id=node_id,
        provenance_rule="brain.workers.process_node.v2",
        payload={"len_body": len(body), "n_chunks_planned": len(chunks)},
    )

    if not chunks:
        events.append(
            event_type="process_done",
            user_id=settings.user_id,
            source="worker",
            node_id=node_id,
            provenance_rule="brain.workers.process_node.v2",
            payload={"n_chunks": 0, "skipped": "empty_body"},
        )
        return {"node_id": node_id, "status": "ok", "n_chunks": 0}

    t0 = time.perf_counter()
    texts = [c.text for c in chunks]
    # Para nodos con título, prefijar mejora recall en BGE-M3 sin alterar
    # el cuerpo persistido en LanceDB.
    title = meta.get("title") or meta.get("name") or ""
    embed_inputs = [f"{title}\n\n{t}".strip() if title else t for t in texts]
    vectors = embed_texts(embed_inputs, model_name=settings.embed_model)

    # Vector del título (o primer chunk si no hay título) para la tabla `nodes`.
    title_input = title or texts[0][:512]
    title_vec = embed_texts([title_input], model_name=settings.embed_model)[0]

    dim = int(vectors.shape[1])
    now = _now_iso()
    node_type = str(meta.get("type") or "knowledge")
    tags = list(meta.get("tags") or [])
    rel_path = str(path.relative_to(vault_root))
    created_at = str(meta.get("created_at") or now)

    chunk_rows = []
    for c, v in zip(chunks, vectors):
        chunk_rows.append(
            {
                "chunk_id": f"{node_id}::c{c.position:03d}",
                "node_id": node_id,
                "user_id": settings.user_id,
                "text": c.text,
                "vector": v.tolist(),
                "tokens": int(c.tokens),
                "position": int(c.position),
                "node_type": node_type,
                "title": title or None,
                "tags": tags,
                "path": rel_path,
                "created_at": created_at,
            }
        )

    node_row = {
        "node_id": node_id,
        "user_id": settings.user_id,
        "node_type": node_type,
        "title": title or None,
        "title_vector": title_vec.tolist(),
        "tags": tags,
        "path": rel_path,
        "summary": body[:480],
        "n_chunks": len(chunks),
        "created_at": created_at,
        "updated_at": now,
    }

    store = LanceStore(settings.lance_path, dim=dim or embed_dim())
    store.delete_node(node_id)
    store.upsert_chunks(chunk_rows)
    store.upsert_node(node_row)
    store.ensure_fts_index()

    # Phase 3b: actualizar grafo de menciones
    n_mentions = 0
    try:
        graph = KuzuGraph(settings.graph_path)
        graph.delete_node(node_id)
        graph.upsert_node(node_id, node_type, title or node_id)

        wikilinks = extract_wikilinks(body)
        if wikilinks:
            # Construir índice title → node_id desde la tabla nodes de LanceDB
            nodes_arrow = store.nodes.to_arrow()
            nodes_dict = nodes_arrow.to_pydict()
            title_to_nid: dict[str, str] = {
                (t.lower() if t else ""): nid
                for t, nid in zip(nodes_dict.get("title", []), nodes_dict.get("node_id", []))
                if t
            }
            for link in wikilinks:
                target_nid = title_to_nid.get(link.lower())
                if target_nid and target_nid != node_id:
                    # Asegurar que el nodo destino existe en el grafo
                    target_title = link
                    target_type = "knowledge"
                    for t, nid, nt in zip(
                        nodes_dict.get("title", []),
                        nodes_dict.get("node_id", []),
                        nodes_dict.get("node_type", []),
                    ):
                        if nid == target_nid:
                            target_title = t or link
                            target_type = nt or "knowledge"
                            break
                    graph.upsert_node(target_nid, target_type, target_title)
                    graph.upsert_mention(node_id, target_nid, weight=1.0)
                    n_mentions += 1
    except Exception:
        pass  # Grafo es best-effort; no bloquea el pipeline principal

    ms = int((time.perf_counter() - t0) * 1000)
    events.append(
        event_type="process_done",
        user_id=settings.user_id,
        source="worker",
        node_id=node_id,
        provenance_rule="brain.workers.process_node.v3",
        payload={"n_chunks": len(chunks), "dim": dim, "ms": ms, "title": bool(title), "n_mentions": n_mentions},
    )
    return {"node_id": node_id, "status": "ok", "n_chunks": len(chunks), "dim": dim, "ms": ms, "n_mentions": n_mentions}
