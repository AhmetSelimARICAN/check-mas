"""OpenAI provider implementation."""

from __future__ import annotations

import os
from typing import Any

from checkmas.providers.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """LLM provider backed by the OpenAI API (GPT-4o-mini, etc.).

    Parameters
    ----------
    api_key : str, optional
        OpenAI API key.  Falls back to ``OPENAI_API_KEY`` env var.
    model : str
        Chat model for completions (default ``gpt-4o-mini``).
    embedding_model : str
        Embedding model (default ``text-embedding-3-small``).

    Example::

        from checkmas import OpenAIProvider
        provider = OpenAIProvider(api_key="sk-...")
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        embedding_model: str = "text-embedding-3-small",
        **client_kwargs: Any,
    ) -> None:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI provider requires the openai package.\n"
                "Install with: pip install checkmas[openai]"
            ) from None

        self._model = model
        self._embedding_model = embedding_model
        self._client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY", ""),
            **client_kwargs,
        )

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = resp.choices[0]
        usage = None
        if resp.usage:
            usage = {
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
                "total_tokens": resp.usage.total_tokens,
            }
        return LLMResponse(
            text=choice.message.content or "",
            model=resp.model,
            usage=usage,
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        truncated = [t[:8000] for t in texts]
        resp = self._client.embeddings.create(
            model=self._embedding_model,
            input=truncated,
        )
        return [item.embedding for item in resp.data]
