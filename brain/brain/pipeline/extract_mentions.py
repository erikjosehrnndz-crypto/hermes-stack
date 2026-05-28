"""Extractor de menciones [[wikilink]] de cuerpos markdown.

Soporta:
  [[Page Name]]          → target = "Page Name"
  [[Page Name|Alias]]    → target = "Page Name" (antes del pipe)
  [[Page Name#heading]]  → target = "Page Name" (antes del hash)
"""
from __future__ import annotations

import re

_WIKILINK = re.compile(r"\[\[([^\]|#]+?)(?:[|#][^\]]+)?\]\]")


def extract_wikilinks(body: str) -> list[str]:
    """Retorna lista de targets únicos de [[wikilink]] del body."""
    seen: dict[str, None] = {}
    for m in _WIKILINK.finditer(body):
        target = m.group(1).strip()
        if target:
            seen[target] = None
    return list(seen)
