"""LlamaFirewall Integration Adapter.

Integrates CHECK-MAS as an additional scanner within Meta's LlamaFirewall
pipeline, adding multi-agent consensus security capabilities that
LlamaFirewall does not natively provide.

CHECK-MAS complements LlamaFirewall's existing scanners:
- **PromptGuard** → jailbreak detection (single agent)
- **AlignmentCheck** → goal hijacking (single agent)
- **CodeShield** → insecure code (single agent)
- **CHECK-MAS** → consensus manipulation, Sybil attacks, coordinated
  deception (multi-agent) ← NEW

Usage with LlamaFirewall::

    from llamafirewall import LlamaFirewall, ScannerType
    from checkmas.adapters.llamafirewall import CheckMASScanner

    # Create CHECK-MAS scanner
    checkmas_scanner = CheckMASScanner(
        provider=OpenAIProvider(),
        phi_mode="graded",
    )

    # Use alongside LlamaFirewall's native scanners
    lf = LlamaFirewall(
        scanners=[ScannerType.PROMPT_GUARD, ScannerType.ALIGNMENT_CHECK]
    )

    # Run LlamaFirewall's checks first, then CHECK-MAS
    lf_result = lf.scan(message)
    checkmas_result = checkmas_scanner.scan_multi_agent(
        claim=task_description,
        responses=agent_responses,
        embeddings=response_embeddings,
    )

Standalone usage (without LlamaFirewall installed)::

    from checkmas.adapters.llamafirewall import CheckMASScanner
    from checkmas import OpenAIProvider

    scanner = CheckMASScanner(provider=OpenAIProvider())
    result = scanner.scan_multi_agent(
        claim="The Earth is round",
        responses=["It is round", "Actually flat", "Flat for sure"],
        embeddings=embeddings_array,
    )
    print(result.blocked_agents)  # [1, 2]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from checkmas.commander import Commander
from checkmas.firewall import SemanticFirewall
from checkmas.providers.base import LLMProvider


@dataclass(frozen=True)
class MultiAgentScanResult:
    """Result of a CHECK-MAS multi-agent scan.

    Compatible with LlamaFirewall's result interface while adding
    multi-agent specific fields.
    """

    is_safe: bool
    blocked_agents: list[int]
    trusted_agents: list[int]
    trust_scores: list[float]
    dynamic_threshold: float
    agent_details: list[dict[str, Any]] = field(default_factory=list)
    consistency_flags: list[str] = field(default_factory=list)


class CheckMASScanner:
    """CHECK-MAS scanner for LlamaFirewall integration.

    Wraps the full Commander pipeline into a scanner interface
    compatible with LlamaFirewall's design patterns.

    Parameters
    ----------
    provider : LLMProvider, optional
        LLM backend. When None, uses rule-based detection only.
    phi_mode : str
        ``"binary"`` or ``"graded"`` (default ``"graded"``).
    evidence_weight : float
        Evidence alignment weight (default 0.4).
    alpha : float
        Bayesian amplification exponent.
    threshold : float
        Minimum trust threshold.
    track_consistency : bool
        Enable multi-round behavioral tracking.
    """

    def __init__(
        self,
        provider: LLMProvider | None = None,
        phi_mode: str = "graded",
        evidence_weight: float = 0.4,
        alpha: float = 2.0,
        threshold: float = 0.25,
        track_consistency: bool = True,
    ) -> None:
        self._commander = Commander(
            provider=provider,
            phi_mode=phi_mode,
            evidence_weight=evidence_weight,
            alpha=alpha,
            threshold=threshold,
            track_consistency=track_consistency,
        )

    def scan_multi_agent(
        self,
        claim: str,
        responses: list[str],
        embeddings: np.ndarray,
        evidence: str = "",
        evidence_embedding: np.ndarray | None = None,
        agent_names: list[str] | None = None,
        stances: list[str | None] | None = None,
    ) -> MultiAgentScanResult:
        """Run CHECK-MAS consensus analysis on multi-agent responses.

        Parameters
        ----------
        claim : str
            The claim or task being discussed.
        responses : list[str]
            One response per agent.
        embeddings : np.ndarray
            Embedding vectors (n_agents, dim).
        evidence : str, optional
            Reference evidence (empty = rhetoric-only mode).
        evidence_embedding : np.ndarray, optional
            Evidence embedding vector.
        agent_names : list[str], optional
            Human-readable agent names.
        stances : list[str | None], optional
            Extracted stances for consistency tracking.

        Returns
        -------
        MultiAgentScanResult
        """
        n = len(responses)
        names = agent_names or [f"Agent_{i}" for i in range(n)]

        result = self._commander.evaluate(
            claim=claim,
            evidence=evidence,
            responses=responses,
            embeddings=embeddings,
            evidence_embedding=evidence_embedding,
            stances=stances,
        )

        agent_details = []
        for i in range(n):
            fw = result.firewall_results[i]
            detail = {
                "name": names[i],
                "index": i,
                "trust_score": result.trust_scores[i],
                "phi_score": fw.score,
                "flagged": fw.flagged,
                "fallacies": fw.fallacies,
                "action": fw.action,
                "reasoning": fw.reasoning,
                "is_blocked": i in result.blocked_indices,
            }
            if result.consistency_reports:
                cr = result.consistency_reports[i]
                detail["consistency_penalty"] = cr.penalty
                detail["consistency_flags"] = cr.flags
            agent_details.append(detail)

        consistency_flags = []
        for cr in result.consistency_reports:
            consistency_flags.extend(cr.flags)

        return MultiAgentScanResult(
            is_safe=len(result.blocked_indices) == 0,
            blocked_agents=result.blocked_indices,
            trusted_agents=result.trusted_indices,
            trust_scores=result.trust_scores,
            dynamic_threshold=result.dynamic_threshold,
            agent_details=agent_details,
            consistency_flags=consistency_flags,
        )

    def scan_single(self, claim: str, argument: str, evidence: str = "") -> dict:
        """Scan a single agent's argument (simplified interface).

        Useful for integrating CHECK-MAS as a custom scanner in
        LlamaFirewall's pipeline for individual message inspection.

        Returns
        -------
        dict
            ``{"flagged": bool, "score": float, "fallacies": [...], ...}``
        """
        fw = self._commander.firewall
        result = fw.check(claim=claim, argument=argument, evidence=evidence)
        return {
            "flagged": result.flagged,
            "score": result.score,
            "fallacies": result.fallacies,
            "action": result.action,
            "reasoning": result.reasoning,
        }

    def reset(self) -> None:
        """Reset Commander state for a new session."""
        self._commander.reset()
