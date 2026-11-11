"""Grounded prompt construction and citation formatting."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def build_grounded_prompt(question: str, chunks: Sequence[dict[str, Any]]) -> str:
    context = "\n\n".join(
        f"[{chunk['document_title']}, page {chunk['page_number']}] {chunk['text']}"
        for chunk in chunks
    )
    return (
        "Answer the question using only the provided context. Cite every factual "
        "claim using [document title, page N]. If the context does not contain "
        "the answer, respond exactly: Not found in the provided documents.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )
