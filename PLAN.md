# Project 2 Plan — Financial/Regulatory RAG Assistant

## Current state

The workspace is currently greenfield and contains only a Python 3.13 virtual environment. The project can therefore be designed cleanly from scratch.

## 1. Define scope and data

- Select 3–5 public Canadian sources:
  - OSFI guidelines
  - FINTRAC guidance
  - Bank of Canada publications
  - Selected bank annual reports
- Record each source URL, title, publication date, download date, and usage/license terms.
- Start with approximately 10–20 PDFs.
- Define supported question types and explicitly exclude legal or financial advice.

**Deliverable:** `data/sources.csv` and downloaded documents under `data/raw/`.

## 2. Establish project structure

```text
CanFinRAG/
├── app/
│   ├── config.py
│   ├── models.py
│   ├── ingestion/
│   ├── retrieval/
│   ├── generation/
│   ├── api/
│   └── logging/
├── data/
│   ├── raw/
│   ├── processed/
│   └── sources.csv
├── evaluation/
│   ├── questions.jsonl
│   ├── evaluate_retrieval.py
│   └── evaluate_answers.py
├── frontend/
│   └── streamlit_app.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## 3. Build the ingestion pipeline

Implement:

1. PDF download with source metadata.
2. Text extraction using PyMuPDF.
3. Cleaning of headers, footers, repeated whitespace, and broken line wraps.
4. Page-aware section detection where possible.
5. Chunking with preserved metadata:
   - document title
   - source URL
   - page number
   - section
   - chunk ID
   - character/token offsets

Compare at least two chunk sizes:

- 400 tokens with 80-token overlap
- 800 tokens with 120-token overlap

**Tests:** extraction, metadata preservation, deterministic chunking, and malformed PDFs.

## 4. Implement indexing

Initial recommendation:

- Embeddings: `sentence-transformers`
- Vector index: FAISS
- Metadata: JSONL or SQLite
- Optional BM25: `rank-bm25`

Create a reproducible indexing command:

```text
python -m app.ingestion.build_index --chunk-size 400
```

Store indexes separately by configuration so experiments are reproducible.

## 5. Implement retrieval experiments

Support:

- Dense vector retrieval
- BM25 retrieval
- Hybrid retrieval using weighted score fusion
- Optional reranking using a cross-encoder

Evaluate multiple configurations:

| Chunk size | Retriever | k |
|---|---|---|
| 400 | Dense | 3, 5, 10 |
| 800 | Dense | 3, 5, 10 |
| 400 | BM25 | 3, 5, 10 |
| 400 | Hybrid | 3, 5, 10 |
| Best chunk size | Hybrid + reranker | 3, 5, 10 |

## 6. Build answer generation

Use an LLM provider abstraction supporting OpenAI or Anthropic.

Prompt requirements:

- Answer only from retrieved context.
- Cite document title and page for every factual claim.
- If evidence is insufficient, respond with: “Not found in the provided documents.”
- Do not invent citations.
- Clearly distinguish quoted facts from synthesis.
- Include retrieved source excerpts in API responses for transparency.

Use environment variables and `.env.example` for configuration. Never commit API keys.

## 7. Create the evaluation set

Create 40–50 manually authored questions with this structure:

```json
{
  "id": "q001",
  "question": "...",
  "expected_answer": "...",
  "source_document": "...",
  "source_pages": [12, 13],
  "source_chunk_ids": ["..."],
  "question_type": "fact_lookup"
}
```

Include:

- Direct factual questions
- Multi-page synthesis
- Definition questions
- Numeric/date questions
- Questions whose answer is intentionally absent
- Ambiguous or difficult retrieval cases

## 8. Measure quality

### Retrieval metrics

- Hit@1
- Hit@3
- Hit@5
- Hit@10
- Mean Reciprocal Rank
- Recall by question type

### Answer metrics

- Citation correctness
- Faithfulness to retrieved context
- Answer completeness
- “Not found” correctness
- Latency
- Token usage/cost where available

Use manual review for a representative sample and optionally an LLM judge, with spot checks against source passages.

## 9. Build the API and frontend

FastAPI endpoints:

```text
GET  /health
POST /query
POST /reindex
GET  /documents
```

`POST /query` should return:

```json
{
  "answer": "...",
  "citations": [
    {
      "document": "...",
      "page": 12,
      "url": "..."
    }
  ],
  "retrieved_chunks": [],
  "latency_ms": 1234
}
```

Streamlit interface:

- Chat input and conversation history
- Answer with inline citations
- Expandable retrieved passages
- Source document links
- Latency display
- Clear disclaimer

## 10. Add observability and testing

Log, without storing secrets:

- Query ID
- Timestamp
- Query text or hashed query
- Retriever configuration
- Retrieved chunk IDs
- Latency
- Answer status
- Error details

Tests should cover:

- Extraction, chunking, retrieval, prompting, and citation formatting
- API behavior with mocked LLM calls
- Evaluation metric calculations
- End-to-end smoke testing with a small fixture corpus

## 11. Containerize and deploy

Create:

- `Dockerfile`
- `docker-compose.yml`
- Separate API and Streamlit services
- Health checks
- Environment-variable configuration
- Persistent index volume

Deploy the API and frontend to a suitable host, then document the demo URL and setup instructions.

## 12. Produce the technical write-up

The README/write-up should include:

1. Problem and corpus scope
2. Architecture diagram
3. Data source and license notes
4. Chunking strategy
5. Retrieval experiments
6. Results comparison table
7. Answer-generation approach
8. Failure cases and mitigations
9. Local setup and deployment
10. Limitations and future improvements

Example results table:

| Chunk size | Retriever | k | Hit@5 | MRR | Faithfulness | Avg latency |
|---:|---|---:|---:|---:|---:|---:|
| 400 | Dense | 5 | — | — | — | — |
| 800 | Dense | 5 | — | — | — | — |
| 400 | Hybrid | 5 | — | — | — | — |
| 400 | Hybrid + reranker | 5 | — | — | — | — |

## Suggested implementation order

1. Project configuration and structure
2. Source registry and PDF ingestion
3. Text extraction and chunking
4. FAISS indexing
5. Dense retrieval
6. Evaluation dataset and retrieval metrics
7. Hybrid retrieval and reranking
8. LLM answer generation and citations
9. FastAPI backend
10. Streamlit frontend
11. Tests, Docker, and deployment
12. Results write-up and failure analysis

## Definition of done

- The assistant answers against the selected public documents.
- Every supported factual answer includes verifiable citations.
- Unsupported questions reliably produce a “not found” response.
- At least two chunk sizes and multiple retrieval strategies are measured.
- Retrieval metrics and answer-quality results are documented.
- FastAPI, Streamlit, tests, Docker configuration, and deployment instructions work from a clean checkout.
