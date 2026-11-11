from fastapi.testclient import TestClient

from app.api.main import create_app


class FakeRetriever:
    def search(self, question: str, k: int) -> list[dict]:
        return [
            {
                "chunk_id": "chunk-1",
                "document_title": "Report",
                "page_number": 2,
                "source_path": "report.pdf",
                "text": "The system is resilient.",
                "score": 1.0,
            }
        ]


class FakeProvider:
    async def generate(self, prompt: str) -> str:
        assert "Report, page 2" in prompt
        return "The system is resilient. [Report, page 2]"


def test_health_endpoint() -> None:
    response = TestClient(create_app()).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_query_endpoint_returns_answer_and_citations() -> None:
    client = TestClient(create_app(FakeRetriever(), FakeProvider()))

    response = client.post("/query", json={"question": "How is the system?"})

    assert response.status_code == 200
    assert response.json()["citations"] == [
        {"document": "Report", "page": 2, "source_path": "report.pdf"}
    ]
