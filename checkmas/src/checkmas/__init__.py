"""CHECK-MAS — Semantic Firewall for Multi-Agent LLM Systems.

Protect your multi-agent pipeline from manipulation, fallacies,
prompt injection, and adversarial agents with a mathematically
grounded trust engine.

Quick start::

    import checkmas

    # Semantic firewall (standalone)
    fw = checkmas.SemanticFirewall()
    result = fw.check(claim=..., argument=..., evidence=...)

    # Full Commander pipeline
    cmd = checkmas.Commander(provider=checkmas.OpenAIProvider())
    result = cmd.evaluate(claim=..., evidence=..., responses=..., embeddings=...)

    # Prompt injection scanner
    scanner = checkmas.PromptGuardScanner()
    result = scanner.scan("Ignore all previous instructions...")

See https://github.com/checkmas/checkmas for full documentation.
"""

from __future__ import annotations

__version__ = "0.2.0"

from checkmas.firewall import SemanticFirewall, FirewallResult, FALLACY_WEIGHTS
from checkmas.commander import Commander, RoundLog
from checkmas.providers.base import LLMProvider, LLMResponse
from checkmas.providers.openai import OpenAIProvider
from checkmas.analysis.consistency import ConsistencyTracker, ConsistencyReport
from checkmas.scanners.promptguard import PromptGuardScanner, ScanResult
from checkmas.scanners.alignment import AlignmentChecker, AlignmentResult
from checkmas.constants import (
    OLLAMA_GUARD_MODEL,
    OLLAMA_DEFAULT_HOST,
    OLLAMA_DEFAULT_PORT,
)

__all__ = [
    "__version__",
    # Core
    "SemanticFirewall",
    "FirewallResult",
    "Commander",
    "RoundLog",
    "FALLACY_WEIGHTS",
    # Providers
    "LLMProvider",
    "LLMResponse",
    "OpenAIProvider",
    # Analysis
    "ConsistencyTracker",
    "ConsistencyReport",
    # Scanners
    "PromptGuardScanner",
    "ScanResult",
    "AlignmentChecker",
    "AlignmentResult",
    # Defaults
    "OLLAMA_GUARD_MODEL",
    "OLLAMA_DEFAULT_HOST",
    "OLLAMA_DEFAULT_PORT",
]
