# CanFinRAG

CanFinRAG is a citation-grounded retrieval-augmented generation assistant for
Canadian financial and regulatory documents.

## Current status

The initial local path is working:

- One Bank of Canada Financial Stability Report is indexed.
- PDF extraction and deterministic page-aware chunking are implemented.
- BM25, dense, and hybrid retrieval implementations are available.
- Ollama generation with `qwen2.5:7b` has been verified locally.
- GitHub Copilot SDK is available as the configured fallback provider.
- FastAPI, Streamlit, logging, and Docker configuration are included.
- The test suite currently passes 14 tests.

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for the phase-by-phase source of
truth.

## Architecture

1. `data/raw/` contains source PDFs registered in `data/sources.csv`.
2. `app/ingestion/pdf.py` extracts page text, detects basic sections, and
   creates deterministic chunks.
3. `app/ingestion/build_index.py` writes chunk metadata to JSONL in
   `data/processed/`.
4. `app/retrieval/` provides BM25, dense, and hybrid retrieval.
5. `app/generation/` builds grounded prompts and calls Ollama first, then
   GitHub Copilot when fallback is enabled.
6. `app/api/main.py` exposes retrieval and grounded generation through FastAPI.
7. `frontend/streamlit_app.py` provides a chat interface.

## Local setup

Use Python 3.13:

```powershell
.\venv\Scripts\python.exe -m pip install -e ".[llm,testing]"
```

Build the processed chunk store:

```powershell
.\venv\Scripts\python.exe -m app.ingestion.build_index `
  data\raw\boc-financial-stability-report-2026.pdf
```

Start Ollama and make sure the model is available:

```powershell
ollama pull qwen2.5:7b
```

Start the API:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.api.main:app --reload
```

Start the frontend in another terminal:

```powershell
.\venv\Scripts\python.exe -m streamlit run frontend\streamlit_app.py
```

The API is available at `http://localhost:8000`; the Streamlit UI is normally
available at `http://localhost:8501`.

## Providers

The default provider order is:

1. Ollama at `http://localhost:11434`, model `qwen2.5:7b`
2. GitHub Copilot SDK, model `gpt-5`

Configure these values with environment variables:

- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `COPILOT_MODEL`
- `CANFINRAG_CHUNKS_PATH`
- `CANFINRAG_API_URL`

The Copilot SDK requires its supported runtime and authentication setup. Do not
commit tokens or credentials; local `.env` files are ignored.

## API example

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/query `
  -ContentType "application/json" `
  -Body '{"question":"What does the report say about financial stability?","k":5}'
```

Responses include the answer, retrieved chunks, source pages, and latency.
Answers with citations outside the retrieved pages are rejected.

## Testing

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

The current suite covers extraction, chunking, retrieval, metrics, providers,
citation validation, and API behavior.

## Evaluation and limitations

The initial evaluation set contains eight manually authored questions for the
currently downloaded report, including an intentionally absent question.
Expand this to 40-50 questions and add the remaining approved sources before
using retrieval metrics as a meaningful benchmark.

Known limitations:

- Only one source document is currently downloaded.
- Source terms and licensing review are pending.
- Dense retrieval has an injected encoder interface but no benchmarked
  production embedding model yet.
- Docker Compose is configured but has not been executed in this environment.
- The system is a research/demo application, not legal or financial advice.
