"""Project-wide defaults (guard targets, Ollama, etc.).

**Guard model (local, preferred):** pull and run with Ollama::

    ollama run llama-guard3

Use :data:`OLLAMA_GUARD_MODEL` when wiring HTTP/Ollama clients. The
:class:`~checkmas.scanners.promptguard.PromptGuardScanner` default remains
HuggingFace ``Llama-Prompt-Guard-2-86M`` for optional in-process inference;
for deployment we standardize on Ollama ``llama-guard3``.
"""

from __future__ import annotations

# Name as shown by `ollama list` after `ollama run llama-guard3` / `ollama pull`
OLLAMA_GUARD_MODEL: str = "llama-guard3"

OLLAMA_DEFAULT_HOST: str = "127.0.0.1"
OLLAMA_DEFAULT_PORT: int = 11434

__all__ = [
    "OLLAMA_GUARD_MODEL",
    "OLLAMA_DEFAULT_HOST",
    "OLLAMA_DEFAULT_PORT",
]
