import json

import pytest

from app.retrieval.bm25 import BM25Retriever


def test_bm25_retrieves_relevant_chunk(tmp_path) -> None:
    path = tmp_path / "chunks.jsonl"
    chunks = [
        {"chunk_id": "a", "text": "capital requirements protect banks"},
        {"chunk_id": "b", "text": "inflation and monetary policy"},
    ]
    path.write_text(
        "\n".join(json.dumps(chunk) for chunk in chunks),
        encoding="utf-8",
    )

    results = BM25Retriever.from_jsonl(path).search("capital requirements", k=1)

    assert results[0]["chunk_id"] == "a"
    assert "score" in results[0]


def test_bm25_rejects_empty_index() -> None:
    with pytest.raises(ValueError, match="At least one"):
        BM25Retriever([])
