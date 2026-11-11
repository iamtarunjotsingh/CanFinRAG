"""LLM provider adapters for Ollama and GitHub Copilot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ProviderError(RuntimeError):
    """A provider could not produce a response."""


class LLMProvider(Protocol):
    async def generate(self, prompt: str) -> str:
        """Generate one response for a prompt."""


@dataclass(frozen=True)
class OllamaProvider:
    model: str = "qwen2.5:7b"
    base_url: str = "http://localhost:11434"

    async def generate(self, prompt: str) -> str:
        try:
            import httpx
        except ImportError as error:
            raise ProviderError("Ollama support requires the llm dependencies") from error
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url.rstrip('/')}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False,
                    },
                    timeout=120,
                )
                response.raise_for_status()
                content = response.json().get("message", {}).get("content")
        except (OSError, httpx.HTTPError) as error:
            raise ProviderError(f"Ollama is unavailable: {error}") from error
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("Ollama returned an empty response")
        return content.strip()


@dataclass(frozen=True)
class CopilotProvider:
    model: str = "gpt-5"

    async def generate(self, prompt: str) -> str:
        try:
            from copilot import CopilotClient
            from copilot.session import PermissionHandler
            from copilot.session_events import AssistantMessageData

            async with CopilotClient() as client:
                async with await client.create_session(
                    model=self.model,
                    on_permission_request=PermissionHandler.approve_all,
                ) as session:
                    reply = await session.send_and_wait(prompt)
                    if reply and isinstance(reply.data, AssistantMessageData):
                        content = reply.data.content
                    else:
                        content = None
        except (ImportError, OSError, RuntimeError) as error:
            raise ProviderError(f"GitHub Copilot is unavailable: {error}") from error
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("GitHub Copilot returned an empty response")
        return content.strip()


@dataclass(frozen=True)
class FallbackProvider:
    primary: LLMProvider
    secondary: LLMProvider

    async def generate(self, prompt: str) -> str:
        try:
            return await self.primary.generate(prompt)
        except ProviderError as primary_error:
            try:
                return await self.secondary.generate(prompt)
            except ProviderError as secondary_error:
                raise ProviderError(
                    f"Both LLM providers failed. Primary: {primary_error}; "
                    f"secondary: {secondary_error}"
                ) from secondary_error
