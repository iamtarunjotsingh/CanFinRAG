import numpy as np

from app.retrieval.bm25 import BM25Retriever
from app.retrieval.dense import DenseRetriever, HybridRetriever


def encoder(texts):
    return np.array(
        [[1.0, 0.0] if "capital" in text.lower() else [0.0, 1.0] for text in texts]
    )


def test_dense_retriever_returns_semantically_similar_chunk(tmp_path) -> None:
    chunks = [
        {"chunk_id": "a", "text": "capital requirements"},
        {"chunk_id": "b", "text": "monetary policy"},
    ]
    import json

    path = tmp_path / "chunks.jsonl"
    path.write_text("\n".join(json.dumps(item) for item in chunks), encoding="utf-8")
    results = DenseRetriever.from_jsonl(path, encoder).search("capital", encoder, k=1)
    assert results[0]["chunk_id"] == "a"


def test_hybrid_retriever_combines_bm25_and_dense() -> None:
    chunks = [
        {"chunk_id": "a", "text": "capital requirements"},
        {"chunk_id": "b", "text": "monetary policy"},
    ]
    dense = DenseRetriever(chunks, encoder([item["text"] for item in chunks]))
    hybrid = HybridRetriever(BM25Retriever(chunks), dense, encoder)

    assert hybrid.search("capital", k=1)[0]["chunk_id"] == "a"
