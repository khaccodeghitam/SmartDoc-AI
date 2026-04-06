from __future__ import annotations

from typing import Iterable, Sequence

import faiss
import numpy as np


def build_faiss_index(vectors: Sequence[Sequence[float]]) -> faiss.Index:
    array = np.asarray(vectors, dtype="float32")
    if array.ndim != 2:
        raise ValueError("vectors must be a 2D array")
    dimension = array.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(array)
    return index


def search_index(index: faiss.Index, query_vector: Sequence[float], top_k: int = 3):
    query = np.asarray([query_vector], dtype="float32")
    distances, indices = index.search(query, top_k)
    return distances[0].tolist(), indices[0].tolist()
