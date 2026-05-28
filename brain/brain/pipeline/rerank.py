"""Reranker singleton vía FastEmbed TextCrossEncoder.

Modelo: jinaai/jina-reranker-v2-base-multilingual (multilingüe, 1K ctx, ONNX CPU).
Descarga al primer uso; se cachea en el mismo volumen que el embedder (brain_models).
"""
from __future__ import annotations

import threading
from typing import Sequence

import numpy as np


_LOCK = threading.Lock()
_RERANKER = None
_RERANKER_NAME: str | None = None

DEFAULT_RERANKER = "jinaai/jina-reranker-v2-base-multilingual"


def get_reranker(model_name: str = DEFAULT_RERANKER):
    global _RERANKER, _RERANKER_NAME
    if _RERANKER is not None and _RERANKER_NAME == model_name:
        return _RERANKER
    with _LOCK:
        if _RERANKER is not None and _RERANKER_NAME == model_name:
            return _RERANKER
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        _RERANKER = TextCrossEncoder(model_name=model_name)
        _RERANKER_NAME = model_name
        return _RERANKER


def rerank(
    query: str,
    hits: list[dict],
    *,
    model_name: str = DEFAULT_RERANKER,
    text_key: str = "snippet",
    top_k: int | None = None,
) -> list[dict]:
    """Reordena `hits` usando el cross-encoder. Añade `rerank_score` a cada hit.

    Args:
        query: texto de búsqueda original.
        hits:  lista de dicts con al menos `text_key` (e.g. "snippet").
        top_k: si se pasa, trunca el resultado a top_k ítems.
        text_key: campo de hits que contiene el texto a puntuar.

    Returns:
        Lista ordenada por `rerank_score` descendente.
    """
    if not hits:
        return hits

    passages = [h.get(text_key) or "" for h in hits]
    model = get_reranker(model_name)

    # TextCrossEncoder.rerank devuelve una lista de floats en el mismo orden que passages
    scores: list[float] = list(model.rerank(query, passages))

    # Normalizar logits crudos a [0,1] con sigmoid para que sean comparables a cosine sim
    def _sigmoid(x: float) -> float:
        import math
        return 1.0 / (1.0 + math.exp(-x))

    out: list[dict] = []
    for hit, score in zip(hits, scores):
        h = dict(hit)
        h["rerank_score"] = round(_sigmoid(float(score)), 6)
        out.append(h)

    out.sort(key=lambda x: x["rerank_score"], reverse=True)

    if top_k is not None:
        out = out[:top_k]

    return out
