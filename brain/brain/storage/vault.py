"""Vault: Markdown como verdad canónica, git auto-commit.

El vault es un repo git en disco. Cada ingest escribe un .md con frontmatter
y commitea inmediatamente — sin DB en el camino. Cualquier herramienta capaz
de leer Markdown (Obsidian, editor de texto, grep) puede consumirlo.

Layout:
    /data/vault/
    ├── journal/       YYYY-MM-DD.md
    ├── notes/         kn-XXXXXXXX.md
    ├── memories/      cm-XXXXXXXX.md
    └── sources/       clip-YYYY-MM-DD-XXXXXXXX.md
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import frontmatter
from git import Repo


NodeType = Literal["journal", "knowledge", "memory", "source"]

_SUBDIRS: dict[NodeType, str] = {
    "journal": "journal",
    "knowledge": "notes",
    "memory": "memories",
    "source": "sources",
}

_ID_PREFIX: dict[NodeType, str] = {
    "journal": "jn",
    "knowledge": "kn",
    "memory": "cm",
    "source": "src",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _gen_id(node_type: NodeType) -> str:
    return f"{_ID_PREFIX[node_type]}-{secrets.token_hex(4)}"


class Vault:
    """Sincronía total: write → commit → return path. Sin colas internas."""

    def __init__(self, root: str | Path, *, git_remote: str | None = None):
        self.root = Path(root)
        self.git_remote = git_remote
        self._repo: Repo | None = None
        self._init_layout()

    def _init_layout(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for sub in _SUBDIRS.values():
            (self.root / sub).mkdir(parents=True, exist_ok=True)

        if not (self.root / ".git").exists():
            self._repo = Repo.init(self.root, initial_branch="main")
            gitignore = self.root / ".gitignore"
            if not gitignore.exists():
                gitignore.write_text(".obsidian/workspace*\n.DS_Store\n", encoding="utf-8")
            readme = self.root / "README.md"
            if not readme.exists():
                readme.write_text(
                    "# Brain Vault\n\nMarkdown canónico. Reconstruible.\n",
                    encoding="utf-8",
                )
            self._repo.index.add([".gitignore", "README.md"])
            self._repo.index.commit("init: vault skeleton")
        else:
            self._repo = Repo(self.root)

    @property
    def repo(self) -> Repo:
        assert self._repo is not None
        return self._repo

    def write_node(
        self,
        *,
        node_type: NodeType,
        user_id: str,
        body: str,
        tags: list[str] | None = None,
        source: str = "api",
        title: str | None = None,
        node_id: str | None = None,
        extra_meta: dict | None = None,
    ) -> tuple[str, Path]:
        """Escribe un nodo y commitea. Devuelve (node_id, path absoluto).

        - `journal`: si `node_id` está vacío, usa `YYYY-MM-DD` (un archivo por día)
          y appendea al cuerpo existente en vez de sobrescribir.
        - Resto: genera id `<prefix>-<8hex>` salvo que se pase uno.
        """
        if node_type == "journal":
            return self._write_journal(
                user_id=user_id,
                body=body,
                tags=tags or [],
                source=source,
                extra_meta=extra_meta or {},
            )

        if node_id is None:
            node_id = _gen_id(node_type)
        path = self.root / _SUBDIRS[node_type] / f"{node_id}.md"

        now = _now_iso()
        post = frontmatter.Post(
            body,
            **{
                "id": node_id,
                "user_id": user_id,
                "type": node_type,
                "created_at": now,
                "updated_at": now,
                "tags": tags or [],
                "source": source,
                "status": "active",
                "linked_nodes": [],
                **(extra_meta or {}),
            },
        )
        if title:
            post["title"] = title

        path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
        self._commit([path], f"ingest({node_type}): {node_id} [{source}]")
        return node_id, path

    def _write_journal(
        self,
        *,
        user_id: str,
        body: str,
        tags: list[str],
        source: str,
        extra_meta: dict,
    ) -> tuple[str, Path]:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        node_id = f"jn-{today}"
        path = self.root / _SUBDIRS["journal"] / f"{today}.md"
        now = _now_iso()

        if path.exists():
            post = frontmatter.load(path)
            existing_tags = list(dict.fromkeys((post.get("tags") or []) + tags))
            post["tags"] = existing_tags
            post["updated_at"] = now
            post.content = (post.content.rstrip() + f"\n\n## {now}\n\n{body}\n").lstrip()
        else:
            post = frontmatter.Post(
                f"## {now}\n\n{body}\n",
                **{
                    "id": node_id,
                    "user_id": user_id,
                    "type": "journal",
                    "date": today,
                    "created_at": now,
                    "updated_at": now,
                    "tags": tags,
                    "source": source,
                    "status": "active",
                    **extra_meta,
                },
            )

        path.write_text(frontmatter.dumps(post) + "\n", encoding="utf-8")
        self._commit([path], f"journal: {today} [{source}]")
        return node_id, path

    def read_node(self, node_id: str) -> tuple[dict, str] | None:
        """Busca un nodo por id. Devuelve (frontmatter, body) o None."""
        path = self._find_path(node_id)
        if path is None:
            return None
        post = frontmatter.load(path)
        return dict(post.metadata), post.content

    def _find_path(self, node_id: str) -> Path | None:
        if node_id.startswith("jn-"):
            date = node_id[3:]
            p = self.root / _SUBDIRS["journal"] / f"{date}.md"
            return p if p.exists() else None
        for subdir in _SUBDIRS.values():
            p = self.root / subdir / f"{node_id}.md"
            if p.exists():
                return p
        return None

    def search_by_name(self, query: str, k: int = 5) -> list[dict]:
        """Stub Phase 1: fuzzy match en nombre de archivo + primera línea del cuerpo."""
        q = query.lower().strip()
        hits: list[tuple[float, dict]] = []
        for path in self.root.rglob("*.md"):
            if path.name == "README.md":
                continue
            name_score = 1.0 if q in path.stem.lower() else 0.0
            body_score = 0.0
            snippet = ""
            try:
                post = frontmatter.load(path)
                content = post.content
                if q in content.lower():
                    body_score = 0.6
                snippet = content.strip().split("\n", 1)[0][:200]
                meta = dict(post.metadata)
            except Exception:
                meta = {}
                snippet = ""
            score = name_score + body_score
            if score == 0.0:
                continue
            hits.append(
                (
                    score,
                    {
                        "id": meta.get("id") or path.stem,
                        "type": meta.get("type", "unknown"),
                        "path": str(path.relative_to(self.root)),
                        "score": round(score, 3),
                        "snippet": snippet,
                        "tags": meta.get("tags", []),
                    },
                )
            )
        hits.sort(key=lambda x: x[0], reverse=True)
        return [h[1] for h in hits[:k]]

    def _commit(self, paths: list[Path], message: str) -> None:
        rel_paths = [str(p.relative_to(self.root)) for p in paths]
        self.repo.index.add(rel_paths)
        if self.repo.index.diff(self.repo.head.commit if self.repo.head.is_valid() else None):
            self.repo.index.commit(message)
        if self.git_remote:
            try:
                self.repo.git.push(self.git_remote, "main")
            except Exception:
                pass
