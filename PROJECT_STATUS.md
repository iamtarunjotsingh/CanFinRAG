# CanFinRAG Project Status

This file is the source of truth for the current implementation phase. Update it
when a phase starts, when work is completed, and when a blocker is discovered.
Before starting a new phase, read this file and confirm that its prerequisites
are complete.

## Current status

- **Last updated:** 2026-11-11
- **Current phase:** Phase 3 - Indexing and retrieval
- **Phase status:** In progress
- **Overall status:** Initial ingestion and BM25 baseline are working
- **Overall estimate:** 35-40%

## Phase tracking

| Phase | Status | Outcome |
|---|---|---|
| 0. Planning and initial source registry | Complete | Plan and source registry exist; one PDF is downloaded |
| 1. Project structure and configuration | Complete | Planned directories and minimal Python project configuration created and validated |
| 2. Source ingestion and chunking | Complete* | Extract, clean, and chunk available source PDFs with page metadata |
| 3. Indexing and retrieval | In progress | Build reproducible chunk storage and dense, BM25, and hybrid retrieval |
| 4. Evaluation dataset and metrics | Not started | Add questions and retrieval/answer quality measurements |
| 5. Answer generation and citations | Not started | Add provider abstraction and grounded citation responses |
| 6. API and frontend | Not started | Implement FastAPI and Streamlit interfaces |
| 7. Testing, observability, and deployment | Not started | Add tests, logging, Docker, and deployment configuration |
| 8. Technical write-up | Not started | Document architecture, results, limitations, and setup |

## Completed work

- Created [PLAN.md](PLAN.md) with scope, architecture, implementation order,
  evaluation requirements, and definition of done.
- Created [data/sources.csv](data/sources.csv) with six planned Canadian
  financial/regulatory sources.
- Downloaded
  [data/raw/boc-financial-stability-report-2026.pdf](data/raw/boc-financial-stability-report-2026.pdf).
- Created a Python 3.13 virtual environment in `venv`.
- Installed the declared runtime and testing dependencies.
- Implemented page-aware extraction, cleanup, section detection, and deterministic
  token-based chunking in `app/ingestion/pdf.py`.
- Added four focused ingestion tests; all pass with `pytest -q`.
- Added `app/ingestion/build_index.py` and persisted 47 chunks to
  `data/processed/chunks.jsonl`.
- Added a BM25 retriever in `app/retrieval/bm25.py`.
- Added retrieval tests; the full suite now passes with 6 tests.

## Completed Phase 1 tasks

- [x] Create the planned application, evaluation, frontend, and test directories.
- [x] Add minimal package configuration and dependency declarations.
- [x] Keep source data and generated indexes outside application code.
- [x] Validate the initial project layout and parse `pyproject.toml`.

## Completed Phase 2 tasks

- [x] Install the core runtime and testing dependencies.
- [x] Implement page-aware PDF extraction and deterministic chunking.
- [x] Preserve source, page, section, and chunk metadata.
- [x] Add focused extraction and chunking tests.

`*` Phase 2 is complete for the currently downloaded document. Additional
documents can be ingested using the same pipeline after their URLs and terms
are confirmed.

## Current Phase 3 tasks

- [x] Persist extracted chunks as JSONL under `data/processed/`.
- [x] Implement initial BM25 indexing and retrieval.
- [x] Add a reproducible indexing command.
- [x] Add focused retrieval tests.
- [ ] Add dense vector retrieval.
- [ ] Add hybrid score fusion and retrieval comparison experiments.

## Blockers and risks

- Five planned sources still need documents or finalized download URLs.
- Source terms and licensing review is pending.
- No Git repository is initialized in this workspace.

## Next step

After the Phase 3 tasks are complete, update this file to mark Phase 3 complete
and move to **Phase 4 - Evaluation dataset and metrics**. Do not start a later
phase while this file still shows an incomplete prerequisite.

## Update log

| Date | Change |
|---|---|
| 2026-11-11 | Created the status file and started Phase 1. |
| 2026-11-11 | Completed Phase 1; validated project layout and started Phase 2. |
| 2026-11-11 | Installed dependencies, implemented PDF ingestion/chunking, and passed 4 tests. |
| 2026-11-11 | Marked Phase 3 in progress after confirming Phase 2 completion. |
| 2026-11-11 | Persisted 47 chunks, added BM25 retrieval, and passed 6 tests. |
