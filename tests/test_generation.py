import asyncio

from app.generation.prompting import build_grounded_prompt, has_supported_citations
from app.generation.providers import FallbackProvider, ProviderError


def test_grounded_prompt_requires_citations_and_not_found_response() -> None:
    prompt = build_grounded_prompt(
        "What is the risk?",
        [
            {
                "document_title": "Report",
                "page_number": 2,
                "text": "The risk is increasing.",
            }
        ],
    )

    assert "[document title, page N]" in prompt
    assert "Not found in the provided documents." in prompt
    assert "[Report, page 2]" in prompt
    assert has_supported_citations("Answer [Report, page 2]", [{"page_number": 2}])
    assert not has_supported_citations("Answer [Report, page 9]", [{"page_number": 2}])


def test_fallback_provider_uses_secondary_after_primary_failure() -> None:
    class Failing:
        async def generate(self, prompt: str) -> str:
            raise ProviderError("offline")

    class Working:
        async def generate(self, prompt: str) -> str:
            return "answer"

    result = asyncio.run(FallbackProvider(Failing(), Working()).generate("question"))
    assert result == "answer"
