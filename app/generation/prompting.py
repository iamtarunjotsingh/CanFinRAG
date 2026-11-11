"""Grounded prompt construction and citation formatting."""

from __future__ import annotations

from collections.abc import Sequence
import re
from typing import Any


def build_grounded_prompt(question: str, chunks: Sequence[dict[str, Any]]) -> str:
    context = "\n\n".join(
        f"[{chunk['document_title']}, page {chunk['page_number']}] {chunk['text']}"
        for chunk in chunks
    )
    allowed_citations = ", ".join(
        f"[{chunk['document_title']}, page {chunk['page_number']}]"
        for chunk in chunks
    )
    return (
        "Answer the question using only the provided context. Cite every factual "
        "claim using [document title, page N]. If the context does not contain "
        "the answer, respond exactly: Not found in the provided documents. "
        f"Only use these citations: {allowed_citations}\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )


def has_supported_citations(answer: str, chunks: Sequence[dict[str, Any]]) -> bool:
    """Return whether every cited page belongs to the retrieved context."""
    if answer.strip() == "Not found in the provided documents.":
        return True
    cited_pages = {
        int(page) for page in re.findall(r"\[.*?,\s*page\s+(\d+)\]", answer, re.IGNORECASE)
    }
    retrieved_pages = {int(chunk["page_number"]) for chunk in chunks}
    return bool(cited_pages) and cited_pages.issubset(retrieved_pages)
