from pathlib import Path

import pytest

from app.ingestion.pdf import PageText, chunk_pages, clean_text, extract_pages


def test_clean_text_repairs_line_wraps_and_normalizes_whitespace() -> None:
    assert clean_text("Risk-\n management\n\nis important.") == "Riskmanagement is important."


def test_chunking_preserves_page_metadata_and_is_deterministic() -> None:
    pages = [
        PageText(
            document_title="Report",
            source_path="report.pdf",
            page_number=2,
            text="one two three four five six",
            section="2 Overview",
        )
    ]

    first = list(chunk_pages(pages, chunk_size=4, overlap=1))
    second = list(chunk_pages(pages, chunk_size=4, overlap=1))

    assert first == second
    assert [chunk.text for chunk in first] == [
        "one two three four",
        "four five six",
    ]
    assert all(chunk.page_number == 2 for chunk in first)
    assert all(chunk.section == "2 Overview" for chunk in first)


def test_chunking_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError, match="overlap"):
        list(chunk_pages([], chunk_size=4, overlap=4))


def test_extract_pages_reads_downloaded_report() -> None:
    path = Path("data/raw/boc-financial-stability-report-2026.pdf")
    pages = extract_pages(path, "Financial Stability Report—2026")

    assert len(pages) > 1
    assert pages[0].page_number == 1
    assert pages[0].document_title == "Financial Stability Report—2026"
    assert pages[0].text
