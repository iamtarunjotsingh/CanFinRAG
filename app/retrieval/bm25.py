"""BM25 retrieval over the persisted JSONL chunk store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi


class BM25Retriever:
    def __init__(self, chunks: list[dict[str, Any]]) -> None:
        if not chunks:
            raise ValueError("At least one chunk is required")
        self.chunks = chunks
        self.index = BM25Okapi([chunk["text"].lower().split() for chunk in chunks])

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "BM25Retriever":
        with Path(path).open(encoding="utf-8") as source:
            chunks = [json.loads(line) for line in source if line.strip()]
        return cls(chunks)

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        if k <= 0:
            raise ValueError("k must be positive")
        scores = self.index.get_scores(query.lower().split())
        ranked = sorted(
            enumerate(scores), key=lambda item: (-float(item[1]), item[0])
        )[:k]
        return [
            {**self.chunks[index], "score": float(score)}
            for index, score in ranked
        ]
