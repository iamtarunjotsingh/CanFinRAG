"""FastAPI application for grounded document questions."""

from __future__ import annotations

import os
import logging
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.generation.prompting import build_grounded_prompt, has_supported_citations
from app.generation.providers import (
    CopilotProvider,
    FallbackProvider,
    OllamaProvider,
    ProviderError,
)
from app.retrieval.bm25 import BM25Retriever

logger = logging.getLogger("canfinrag.api")


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=20)


class Citation(BaseModel):
    document: str
    page: int
    source_path: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved_chunks: list[dict[str, Any]]
    latency_ms: int


def create_app(retriever: BM25Retriever | None = None, provider: Any = None) -> FastAPI:
    app = FastAPI(title="CanFinRAG API", version="0.1.0")
    app.state.retriever = retriever
    app.state.provider = provider

    @app.middleware("http")
    async def request_logging(request, call_next):
        request_id = str(uuid.uuid4())
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed request_id=%s method=%s path=%s",
                request_id,
                request.method,
                request.url.path,
            )
            raise
        logger.info(
            "request_completed request_id=%s method=%s path=%s status=%s latency_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            round((time.perf_counter() - started) * 1000),
        )
        response.headers["X-Request-ID"] = request_id
        return response

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/query", response_model=QueryResponse)
    async def query(request: QueryRequest) -> QueryResponse:
        started = time.perf_counter()
        active_retriever = app.state.retriever or _load_retriever()
        active_provider = app.state.provider or _build_provider()
        chunks = active_retriever.search(request.question, k=request.k)
        try:
            answer = await active_provider.generate(
                build_grounded_prompt(request.question, chunks)
            )
        except ProviderError as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        if not has_supported_citations(answer, chunks):
            raise HTTPException(
                status_code=502,
                detail="The provider returned unsupported or missing citations.",
            )
        citations = [
            Citation(
                document=chunk["document_title"],
                page=chunk["page_number"],
                source_path=chunk["source_path"],
            )
            for chunk in chunks
        ]
        return QueryResponse(
            answer=answer,
            citations=citations,
            retrieved_chunks=chunks,
            latency_ms=round((time.perf_counter() - started) * 1000),
        )

    return app


def _load_retriever() -> BM25Retriever:
    path = Path(os.getenv("CANFINRAG_CHUNKS_PATH", "data/processed/chunks.jsonl"))
    if not path.exists():
        raise HTTPException(status_code=503, detail=f"Chunk index not found: {path}")
    return BM25Retriever.from_jsonl(path)


def _build_provider() -> Any:
    ollama = OllamaProvider(
        model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )
    copilot = CopilotProvider(model=os.getenv("COPILOT_MODEL", "gpt-5"))
    return FallbackProvider(ollama, copilot)


app = create_app()
