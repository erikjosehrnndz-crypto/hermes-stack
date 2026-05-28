#!/usr/bin/env python3
"""Sincroniza /root/wiki/**/*.md → brain via POST /api/v1/ingest/text.

Uso desde el host (no desde dentro del contenedor):
    BRAIN_API_TOKEN=$(grep ^BRAIN_API_TOKEN /root/.env | cut -d= -f2)
    python3 /root/brain/scripts/sync_wiki.py
    # opcional: --base http://127.0.0.1:8765 --wiki /root/wiki

Política:
- type = "knowledge" (todas las páginas de la wiki).
- title = nombre del archivo (sin extensión) o frontmatter `name`.
- tags = [carpeta_padre] (entities|concepts|topics|sources) + tags del frontmatter.
- source = "wiki".
- Idempotente: el worker borra el node_id previo antes de reinsertar.
  El node_id estable se deriva de la ruta para evitar duplicar entre runs.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
from pathlib import Path

import frontmatter
import httpx


def _stable_node_id(rel_path: str) -> str:
    h = hashlib.sha1(rel_path.encode("utf-8")).hexdigest()[:8]
    return f"kn-wiki-{h}"


def _iter_wiki(wiki_root: Path):
    for p in sorted(wiki_root.rglob("*.md")):
        if p.name.startswith("_"):
            continue  # _index.md, _schema.md
        yield p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.environ.get("BRAIN_BASE", "http://127.0.0.1:8765"))
    ap.add_argument("--wiki", default="/root/wiki", type=Path)
    ap.add_argument("--token", default=os.environ.get("BRAIN_API_TOKEN"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.token:
        print("BRAIN_API_TOKEN no definido (env o --token).", file=sys.stderr)
        return 2

    wiki_root: Path = args.wiki
    if not wiki_root.exists():
        print(f"wiki no existe: {wiki_root}", file=sys.stderr)
        return 2

    headers = {"Authorization": f"Bearer {args.token}"}
    url = f"{args.base.rstrip('/')}/api/v1/ingest/text"

    files = list(_iter_wiki(wiki_root))
    print(f"wiki: {len(files)} archivos en {wiki_root}")

    sent = 0
    errors = 0
    with httpx.Client(timeout=30.0) as client:
        for p in files:
            rel = p.relative_to(wiki_root).as_posix()
            try:
                post = frontmatter.load(p)
                body = (post.content or "").strip()
                meta = dict(post.metadata)
            except Exception as e:
                print(f"  ! parse {rel}: {e}", file=sys.stderr)
                errors += 1
                continue

            if not body:
                print(f"  - skip vacío: {rel}")
                continue

            folder = p.parent.name
            title = str(meta.get("name") or p.stem.replace("_", " "))
            tags = sorted(
                {folder} | {str(t) for t in (meta.get("tags") or [])}
            )

            node_id = _stable_node_id(rel)
            payload = {
                "text": f"# {title}\n\n{body}",
                "type": "knowledge",
                "tags": tags,
                "source": "wiki",
                "title": title,
                "node_id": node_id,
            }

            if args.dry_run:
                print(f"  · {rel} → {node_id} (tags={tags})")
                sent += 1
                continue

            try:
                r = client.post(url, json=payload, headers=headers)
                if r.status_code not in (200, 202):
                    print(f"  ! {rel}: HTTP {r.status_code} {r.text[:120]}", file=sys.stderr)
                    errors += 1
                    continue
                got = r.json()
                print(f"  · {rel} → {got.get('id')} (job {got.get('job_id')})")
                sent += 1
                # Suaviza la carga al worker para que termine cada job antes
                # de encolar el siguiente. BGE-M3 en CPU tarda ~1-3s/nodo.
                time.sleep(0.05)
            except httpx.HTTPError as e:
                print(f"  ! {rel}: {e}", file=sys.stderr)
                errors += 1

    print(f"sent={sent} errors={errors}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
