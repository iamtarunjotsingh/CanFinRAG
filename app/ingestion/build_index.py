"""Build a reproducible JSONL chunk store from a PDF source."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.ingestion.pdf import chunk_pages, extract_pages


def build_chunk_store(
    source_path: str | Path,
    output_path: str | Path,
    document_title: str | None = None,
    chunk_size: int = 400,
    overlap: int = 80,
) -> int:
    pages = extract_pages(source_path, document_title)
    chunks = chunk_pages(pages, chunk_size=chunk_size, overlap=overlap)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with destination.open("w", encoding="utf-8") as output:
        for chunk in chunks:
            output.write(json.dumps(chunk.__dict__, ensure_ascii=False) + "\n")
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/processed/chunks.jsonl"))
    parser.add_argument("--title")
    parser.add_argument("--chunk-size", type=int, default=400)
    parser.add_argument("--overlap", type=int, default=80)
    args = parser.parse_args()
    count = build_chunk_store(
        args.source,
        args.output,
        document_title=args.title,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
    )
    print(f"Wrote {count} chunks to {args.output}")


if __name__ == "__main__":
    main()
