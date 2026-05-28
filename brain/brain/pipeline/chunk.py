"""Late-chunking simple: agrupa por headings/párrafos respetando un cap de tokens.

Heurística sin tokenizer pesado: aprox. 4 chars ≈ 1 token (suficiente para
documentos cortos tipo wiki). El embedder real (BGE-M3) trunca a 8192 tokens,
así que con 480 tokens objetivo dejamos margen de sobra.

Política:
- Divide el texto en bloques por líneas en blanco + headings markdown.
- Acumula bloques hasta acercarse al cap; emite chunk y reinicia con overlap.
- Cada chunk recibe `position` (0-indexed) y `tokens` (estimado).
"""
from __future__ import annotations

import re
from dataclasses import dataclass


_HEADING_RE = re.compile(r"^(#{1,6})\s+.+$", re.MULTILINE)


@dataclass(slots=True)
class Chunk:
    position: int
    text: str
    tokens: int


def _approx_tokens(text: str) -> int:
    # ~4 chars/token para inglés, ~3 para español. Promedio 3.5.
    return max(1, len(text) // 4)


def _split_blocks(text: str) -> list[str]:
    """Divide por líneas en blanco; mantiene los headings al inicio de su bloque."""
    raw = re.split(r"\n\s*\n", text.strip())
    blocks: list[str] = []
    for b in raw:
        b = b.strip("\n")
        if b:
            blocks.append(b)
    return blocks


def chunk_text(
    text: str,
    *,
    max_tokens: int = 480,
    overlap_tokens: int = 64,
) -> list[Chunk]:
    """Late-chunking simple. Devuelve chunks ordenados con metadatos mínimos.

    - max_tokens: cap blando por chunk (se respeta a nivel bloque, no a nivel token).
    - overlap_tokens: prefijo del chunk anterior que se mantiene en el siguiente
      para preservar contexto local.
    """
    text = (text or "").strip()
    if not text:
        return []

    blocks = _split_blocks(text)
    if not blocks:
        return []

    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_tokens = 0
    position = 0

    def _flush(carry_text: str = "") -> str:
        nonlocal buf, buf_tokens, position
        if not buf:
            return ""
        body = "\n\n".join(buf).strip()
        if not body:
            buf = []
            buf_tokens = 0
            return ""
        chunks.append(Chunk(position=position, text=body, tokens=_approx_tokens(body)))
        position += 1
        # Construir overlap (últimos `overlap_tokens` aproximados del body)
        if overlap_tokens > 0:
            overlap_chars = overlap_tokens * 4
            overlap = body[-overlap_chars:].lstrip()
        else:
            overlap = ""
        buf = []
        buf_tokens = 0
        if overlap:
            buf.append(overlap)
            buf_tokens = _approx_tokens(overlap)
        if carry_text:
            buf.append(carry_text)
            buf_tokens += _approx_tokens(carry_text)
        return overlap

    for block in blocks:
        btoks = _approx_tokens(block)

        # Bloque solo más grande que el cap: trocear duro por párrafos internos.
        if btoks > max_tokens:
            _flush()
            chunk_chars = max_tokens * 4
            for i in range(0, len(block), chunk_chars):
                piece = block[i : i + chunk_chars].strip()
                if not piece:
                    continue
                chunks.append(
                    Chunk(position=position, text=piece, tokens=_approx_tokens(piece))
                )
                position += 1
            continue

        if buf_tokens + btoks > max_tokens and buf:
            _flush(carry_text=block)
            continue

        buf.append(block)
        buf_tokens += btoks

    _flush()
    return chunks
