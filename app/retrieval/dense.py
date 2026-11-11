"""Dense and hybrid retrieval over persisted chunks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np

Encoder = Callable[[Sequence[str]], np.ndarray]


class DenseRetriever:
    def __init__(self, chunks: list[dict[str, Any]], embeddings: np.ndarray) -> None:
        if not chunks:
            raise ValueError("At least one chunk is required")
        if embeddings.shape[0] != len(chunks):
            raise ValueError("Each chunk must have one embedding")
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        self.chunks = chunks
        self.embeddings = embeddings / np.maximum(norms, 1e-12)

    @classmethod
    def from_jsonl(cls, path: str | Path, encoder: Encoder) -> "DenseRetriever":
        with Path(path).open(encoding="utf-8") as source:
            chunks = [json.loads(line) for line in source if line.strip()]
        return cls(chunks, np.asarray(encoder([chunk["text"] for chunk in chunks])))

    def search(self, query: str, encoder: Encoder, k: int = 5) -> list[dict[str, Any]]:
        if k <= 0:
            raise ValueError("k must be positive")
        query_embedding = np.asarray(encoder([query]))[0]
        query_embedding = query_embedding / max(float(np.linalg.norm(query_embedding)), 1e-12)
        scores = self.embeddings @ query_embedding
        ranked = sorted(
            enumerate(scores), key=lambda item: (-float(item[1]), item[0])
        )[:k]
        return [{**self.chunks[index], "score": float(score)} for index, score in ranked]


class HybridRetriever:
    def __init__(self, bm25: Any, dense: DenseRetriever, encoder: Encoder) -> None:
        self.bm25 = bm25
        self.dense = dense
        self.encoder = encoder

    def search(
        self, query: str, k: int = 5, dense_weight: float = 0.5
    ) -> list[dict[str, Any]]:
        if not 0 <= dense_weight <= 1:
            raise ValueError("dense_weight must be between 0 and 1")
        bm25_results = self.bm25.search(query, k=len(self.bm25.chunks))
        dense_results = self.dense.search(query, self.encoder, k=len(self.dense.chunks))
        bm25_scores = {item["chunk_id"]: item["score"] for item in bm25_results}
        dense_scores = {item["chunk_id"]: item["score"] for item in dense_results}
        all_results = {item["chunk_id"]: item for item in bm25_results + dense_results}
        bm25_max = max((max(bm25_scores.values()), 1e-12))
        dense_max = max((max(dense_scores.values()), 1e-12))
        ranked = []
        for chunk_id, item in all_results.items():
            score = (1 - dense_weight) * bm25_scores.get(chunk_id, 0) / bm25_max
            score += dense_weight * dense_scores.get(chunk_id, 0) / dense_max
            ranked.append({**item, "score": float(score)})
        return sorted(ranked, key=lambda item: (-item["score"], item["chunk_id"]))[:k]
