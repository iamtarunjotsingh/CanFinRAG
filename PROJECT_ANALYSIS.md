# CanFinRAG Project Analysis

## 1. Executive summary

CanFinRAG is a citation-grounded retrieval-augmented generation (RAG)
assistant for Canadian financial and regulatory documents. The current demo
indexes the Bank of Canada *Financial Stability Report—2026*, retrieves
relevant passages, and uses a local Ollama model to generate an answer with
page citations.

The project is intentionally designed as a research/demo system rather than
legal or financial advice. It favors traceability and explicit failure over
uncited or invented answers.

## 2. Current implementation

Implemented components:

- Python 3.13 project configuration in [`pyproject.toml`](pyproject.toml)
- Source registry in [`data/sources.csv`](data/sources.csv)
- PDF extraction and chunking in
  [`app/ingestion/pdf.py`](app/ingestion/pdf.py)
- Reproducible chunk-store command in
  [`app/ingestion/build_index.py`](app/ingestion/build_index.py)
- Persisted JSONL chunks in
  [`data/processed/chunks.jsonl`](data/processed/chunks.jsonl)
- BM25 retrieval in [`app/retrieval/bm25.py`](app/retrieval/bm25.py)
- Dense and hybrid retrieval in
  [`app/retrieval/dense.py`](app/retrieval/dense.py)
- Retrieval metrics in [`evaluation/metrics.py`](evaluation/metrics.py)
- Initial evaluation questions in
  [`evaluation/questions.jsonl`](evaluation/questions.jsonl)
- Ollama and GitHub Copilot providers in
  [`app/generation/providers.py`](app/generation/providers.py)
- Grounded prompt and citation validation in
  [`app/generation/prompting.py`](app/generation/prompting.py)
- FastAPI service in [`app/api/main.py`](app/api/main.py)
- Streamlit client in [`frontend/streamlit_app.py`](frontend/streamlit_app.py)
- Docker configuration in [`Dockerfile`](Dockerfile) and
  [`docker-compose.yml`](docker-compose.yml)

The current test suite contains 14 passing tests.

## 3. Architecture and data flow

```text
PDF sources
    |
    v
PyMuPDF extraction
    |
    v
clean text + page metadata
    |
    v
deterministic token chunks
    |
    v
JSONL chunk store
    |
    v
BM25 / dense / hybrid retrieval
    |
    v
grounded prompt with source pages
    |
    v
Ollama qwen2.5:7b
    |  fallback
    v
GitHub Copilot SDK
    |
    v
answer + validated citations
```

The API retrieves chunks first, constructs a prompt from only those chunks,
calls the configured provider, validates cited page numbers, and returns the
answer with the retrieved evidence.

## 4. Ingestion and chunking

### PDF extraction

[`extract_pages()`](app/ingestion/pdf.py) uses PyMuPDF to read each page and
preserves:

- Document title
- Source path
- One-based page number
- Extracted text
- Basic section metadata

Page boundaries are preserved because citations need to point back to a
specific document page.

### Text cleaning

[`clean_text()`](app/ingestion/pdf.py) removes soft hyphens, joins broken line
wraps, normalizes whitespace, and strips leading/trailing whitespace. Cleaning
is intentionally conservative so source meaning is not rewritten.

### Chunking

[`chunk_pages()`](app/ingestion/pdf.py) uses whitespace-token windows. The
default is 400 tokens with an 80-token overlap.

Why:

- A chunk must be small enough for focused retrieval.
- Overlap reduces the chance of splitting a relevant statement at a boundary.
- Page-local chunks make citation attribution straightforward.
- Deterministic token windows make experiments reproducible.

Each chunk stores a deterministic ID, page, section, source path, text, and
token offsets. The current report produces 47 chunks.

## 5. Retrieval techniques

### BM25

[`BM25Retriever`](app/retrieval/bm25.py) is the implemented baseline.

Why BM25:

- Strong for exact financial and regulatory terminology.
- Works without a model download or GPU.
- Easy to inspect and reproduce.
- Useful for terms, acronyms, dates, and numeric concepts.

### Dense retrieval

[`DenseRetriever`](app/retrieval/dense.py) accepts an injected encoder and
compares normalized vectors using cosine similarity.

Why dense retrieval:

- Finds semantically similar wording even when exact terms differ.
- Helps with paraphrased questions.
- Keeps the encoder separate from retrieval so the embedding model can be
  replaced or benchmarked.

The current implementation has a tested encoder interface, but a production
embedding model has not yet been benchmarked.

### Hybrid retrieval

[`HybridRetriever`](app/retrieval/dense.py) combines normalized BM25 and dense
scores.

Why hybrid retrieval:

- BM25 provides lexical precision.
- Dense retrieval provides semantic recall.
- Combining both is safer for a mixed corpus containing exact regulatory terms
  and natural-language questions.

## 6. Generation and grounding

### Provider abstraction

[`LLMProvider`](app/generation/providers.py) defines an async `generate()`
contract. The implementations are:

- `OllamaProvider`: local HTTP API, default model `qwen2.5:7b`
- `CopilotProvider`: GitHub Copilot Python SDK
- `FallbackProvider`: tries Ollama first, then Copilot after a provider failure

Why an abstraction:

- The application does not depend on one vendor.
- Local inference can be used for privacy and cost control.
- Copilot provides an alternative when local inference is unavailable.
- Providers can be mocked in tests.

### Grounded prompting

[`build_grounded_prompt()`](app/generation/prompting.py) instructs the model to:

- Use only retrieved context.
- Cite factual claims with document and page.
- Use an exact not-found response when evidence is absent.
- Use only the citations listed from retrieved chunks.

### Citation validation

[`has_supported_citations()`](app/generation/prompting.py) rejects answers
that have no citation or cite a page outside the retrieved context. This is
important because a prompt is guidance, not a guarantee.

The API returns an explicit error instead of silently returning an unsupported
answer.

## 7. API and frontend

### FastAPI

[`app/api/main.py`](app/api/main.py) exposes:

- `GET /health`
- `POST /query`

`POST /query` accepts a question and retrieval `k`, then returns:

- Answer
- Citations
- Retrieved chunks
- Latency in milliseconds

### Streamlit

[`frontend/streamlit_app.py`](frontend/streamlit_app.py) provides:

- Chat history
- Question input
- Answer display
- Source-page display
- API error display

## 8. Observability and deployment

The API logs request ID, method, path, status, and latency without logging
question text or secrets. This balances troubleshooting with privacy.

The Docker setup includes:

- API service
- Streamlit service
- Ollama service
- Ollama model volume
- Health check for Ollama

Docker Compose has not been executed in the current environment because Docker
is not installed there.

## 9. Testing strategy

The tests cover:

- PDF extraction
- Text cleanup
- Deterministic chunking
- Metadata preservation
- Invalid chunk parameters
- BM25 retrieval
- Dense retrieval
- Hybrid retrieval
- Hit@k and reciprocal rank
- Grounded prompt requirements
- Citation validation
- Provider fallback
- API health and query behavior

Run them with:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

## 10. Findings and limitations

### Findings

1. Page-aware chunks are necessary for useful citations.
2. BM25 is a valuable baseline for regulation-heavy text.
3. Provider fallback improves availability but does not remove the need for
   provider-specific authentication.
4. Prompt instructions alone are insufficient; citation validation is required.
5. JSONL is convenient for a small reproducible corpus, while SQLite or a
   vector database may be better at larger scale.

### Limitations

- Only one source document is currently downloaded.
- Five planned source entries still need documents and terms review.
- The evaluation set has eight questions instead of the planned 40-50.
- Dense retrieval lacks a benchmarked production embedding model.
- Citation validation checks page support, not full claim-level entailment.
- Docker configuration is unverified in this environment.
- The system must not be presented as legal or financial advice.

## 11. Recommended next improvements

1. Download and license-review the remaining approved sources.
2. Expand the evaluation set to 40-50 questions.
3. Benchmark chunk sizes and embedding models.
4. Add claim-level faithfulness evaluation.
5. Add persistent index versioning and SQLite metadata.
6. Validate Docker Compose on a Docker-enabled machine.
7. Add authentication and rate limiting before public deployment.
