"""Abstract base for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponse:
    """Standardized LLM response container."""

    text: str
    model: str
    usage: dict | None = None


class LLMProvider(ABC):
    """Protocol that any LLM backend must implement to power CHECK-MAS.

    Subclass this and pass an instance to ``SemanticFirewall`` or ``Commander``.
    Only two methods are required: ``complete`` and ``embed``.

    Example — writing a custom provider::

        class MyProvider(LLMProvider):
            def complete(self, system, user, **kw) -> LLMResponse:
                text = my_model.generate(system + user)
                return LLMResponse(text=text, model="my-model")

            def embed(self, texts, **kw) -> list[list[float]]:
                return my_model.embed_batch(texts)
    """

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        """Generate a chat completion.

        Parameters
        ----------
        system_prompt : str
            System-level instruction.
        user_prompt : str
            User-level content to analyze.
        temperature : float
            Sampling temperature (lower = more deterministic).
        max_tokens : int
            Maximum tokens in the response.
        """

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for a batch of texts.

        Parameters
        ----------
        texts : list[str]
            Texts to embed.

        Returns
        -------
        list[list[float]]
            One embedding vector per input text.
        """
