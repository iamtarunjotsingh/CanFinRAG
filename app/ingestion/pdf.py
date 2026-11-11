"""PDF extraction and deterministic, page-aware chunking."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import fitz


@dataclass(frozen=True)
class PageText:
    document_title: str
    source_path: str
    page_number: int
    text: str
    section: str | None = None


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_title: str
    source_path: str
    page_number: int
    section: str | None
    text: str
    start_token: int
    end_token: int


def clean_text(text: str) -> str:
    """Normalize PDF whitespace and repair line breaks inside words/sentences."""
    text = text.replace("\u00ad", "")
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _section_for_page(text: str) -> str | None:
    for line in text.splitlines():
        candidate = line.strip()
        if 3 <= len(candidate) <= 120 and not candidate.endswith((".", ",", ";", ":")):
            if candidate.isupper() or re.match(r"^\d+(?:\.\d+)*\s+\S+", candidate):
                return candidate
    return None


def extract_pages(path: str | Path, document_title: str | None = None) -> list[PageText]:
    """Extract cleaned text and basic section metadata from each PDF page."""
    pdf_path = Path(path)
    title = document_title or pdf_path.stem
    pages: list[PageText] = []
    with fitz.open(pdf_path) as document:
        for index, page in enumerate(document):
            raw_text = page.get_text("text")
            pages.append(
                PageText(
                    document_title=title,
                    source_path=str(pdf_path),
                    page_number=index + 1,
                    text=clean_text(raw_text),
                    section=_section_for_page(raw_text),
                )
            )
    return pages


def _chunk_id(page: PageText, start: int, end: int, text: str) -> str:
    digest = hashlib.sha1(
        f"{page.source_path}|{page.page_number}|{start}|{end}|{text}".encode("utf-8")
    ).hexdigest()[:12]
    return f"{Path(page.source_path).stem}-p{page.page_number}-{digest}"


def chunk_pages(
    pages: list[PageText], chunk_size: int = 400, overlap: int = 80
) -> Iterator[Chunk]:
    """Yield deterministic whitespace-token chunks without crossing page boundaries."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    step = chunk_size - overlap
    for page in pages:
        tokens = page.text.split()
        for start in range(0, len(tokens), step):
            end = min(start + chunk_size, len(tokens))
            if start >= end:
                continue
            text = " ".join(tokens[start:end])
            yield Chunk(
                chunk_id=_chunk_id(page, start, end, text),
                document_title=page.document_title,
                source_path=page.source_path,
                page_number=page.page_number,
                section=page.section,
                text=text,
                start_token=start,
                end_token=end,
            )
            if end == len(tokens):
                break
