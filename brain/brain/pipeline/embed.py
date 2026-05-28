"""Embedder dense vía FastEmbed (ONNX, sin GPU).

Modelo por defecto: intfloat/multilingual-e5-large (1024 dims, normalizado, multilingüe, 8192 ctx).

Singleton perezoso: el modelo se descarga la primera vez a
`FASTEMBED_CACHE_PATH` (montado como volumen `brain_models` para no perderlo
entre reinicios). Sucesivas llamadas reutilizan la instancia en memoria.
"""
from __future__ import annotations

import threading
from typing import Iterable

import numpy as np


_LOCK = threading.Lock()
_MODEL = None
_MODEL_NAME: str | None = None
_DIM: int | None = None


def get_embedder(model_name: str = "intfloat/multilingual-e5-large"):
    """Devuelve un `TextEmbedding` de FastEmbed. Carga perezosa, thread-safe."""
    global _MODEL, _MODEL_NAME
    if _MODEL is not None and _MODEL_NAME == model_name:
        return _MODEL
    with _LOCK:
        if _MODEL is not None and _MODEL_NAME == model_name:
            return _MODEL
        from fastembed import TextEmbedding  # import local: evita coste al import del paquete

        _MODEL = TextEmbedding(model_name=model_name)
        _MODEL_NAME = model_name
        return _MODEL


def embed_texts(
    texts: Iterable[str],
    *,
    model_name: str = "intfloat/multilingual-e5-large",
    batch_size: int = 16,
) -> np.ndarray:
    """Embebe una lista de textos y devuelve matriz `(n, dim)` float32 normalizada."""
    global _DIM
    model = get_embedder(model_name)
    items = [t if t else " " for t in texts]
    if not items:
        return np.zeros((0, _DIM or 1024), dtype=np.float32)
    vecs = list(model.embed(items, batch_size=batch_size))
    arr = np.asarray(vecs, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    arr = arr / norms
    _DIM = arr.shape[1]
    return arr


def embed_query(
    text: str,
    *,
    model_name: str = "intfloat/multilingual-e5-large",
) -> np.ndarray:
    """Embebe una sola query. Para BGE-M3 no requiere prefijo especial."""
    global _DIM
    model = get_embedder(model_name)
    vec = next(iter(model.query_embed([text])))
    arr = np.asarray(vec, dtype=np.float32)
    n = float(np.linalg.norm(arr))
    if n > 0:
        arr = arr / n
    _DIM = arr.shape[0]
    return arr


def embed_dim() -> int:
    return _DIM or 1024
