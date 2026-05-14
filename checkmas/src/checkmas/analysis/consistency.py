"""Multi-round behavioral consistency analysis.

Tracks agent behavior across rounds to detect manipulation patterns
that are invisible in single-round analysis:

- **Stance Flipping**: Agent changes position between rounds.
- **Confidence Anomaly**: Over/under-confident relative to evidence.
- **Collusion Detection**: Suspiciously similar responses from agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class AgentProfile:
    """Accumulated behavioral profile for one agent."""

    stances: list[str | None] = field(default_factory=list)
    trust_history: list[float] = field(default_factory=list)
    flagged_rounds: list[int] = field(default_factory=list)
    response_history: list[str] = field(default_factory=list)
    flip_count: int = 0
    total_rounds: int = 0


@dataclass(frozen=True)
class ConsistencyReport:
    """Per-agent behavioral consistency assessment."""

    agent_index: int
    flip_score: float
    collusion_score: float
    penalty: float
    flags: list[str] = field(default_factory=list)


class ConsistencyTracker:
    """Tracks multi-round behavioral patterns for a set of agents.

    Parameters
    ----------
    n_agents : int
        Number of agents to track.
    flip_penalty : float
        Trust penalty per detected stance flip (default 0.15).
    collusion_threshold : float
        Cosine similarity above which two agents are flagged for
        potential collusion (default 0.95).
    """

    def __init__(
        self,
        n_agents: int,
        flip_penalty: float = 0.15,
        collusion_threshold: float = 0.95,
    ) -> None:
        self.n_agents = n_agents
        self.flip_penalty = flip_penalty
        self.collusion_threshold = collusion_threshold
        self.profiles: list[AgentProfile] = [
            AgentProfile() for _ in range(n_agents)
        ]
        self._round_count = 0

    def record_round(
        self,
        responses: list[str],
        stances: list[str | None],
        embeddings: np.ndarray | None = None,
        trust_scores: list[float] | None = None,
        flagged_indices: list[int] | None = None,
    ) -> list[ConsistencyReport]:
        """Record one round of agent behavior and produce reports.

        Parameters
        ----------
        responses : list[str]
            Agent responses for this round.
        stances : list[str | None]
            Extracted stances (e.g., "SUPPORTED", "REFUTED", None).
        embeddings : np.ndarray, optional
            Response embedding vectors (n_agents, dim). Used for
            collusion detection.
        trust_scores : list[float], optional
            Trust scores from Commander for this round.
        flagged_indices : list[int], optional
            Indices of agents flagged by the firewall.

        Returns
        -------
        list[ConsistencyReport]
            One report per agent.
        """
        self._round_count += 1

        for i in range(self.n_agents):
            p = self.profiles[i]
            p.total_rounds = self._round_count
            p.stances.append(stances[i] if i < len(stances) else None)
            p.response_history.append(responses[i] if i < len(responses) else "")
            if trust_scores and i < len(trust_scores):
                p.trust_history.append(trust_scores[i])
            if flagged_indices and i in flagged_indices:
                p.flagged_rounds.append(self._round_count)

            if len(p.stances) >= 2:
                prev = p.stances[-2]
                curr = p.stances[-1]
                if prev and curr and prev != curr:
                    p.flip_count += 1

        collusion_scores = self._detect_collusion(embeddings) if embeddings is not None else [0.0] * self.n_agents

        reports = []
        for i in range(self.n_agents):
            p = self.profiles[i]
            flags: list[str] = []

            flip_score = p.flip_count / max(p.total_rounds - 1, 1)
            if p.flip_count > 0:
                flags.append(f"stance_flip(count={p.flip_count})")

            cs = collusion_scores[i]
            if cs > self.collusion_threshold:
                flags.append(f"collusion_suspect(sim={cs:.3f})")

            flagged_ratio = len(p.flagged_rounds) / max(p.total_rounds, 1)
            if flagged_ratio > 0.5 and p.total_rounds >= 2:
                flags.append(f"repeated_offender(flagged={len(p.flagged_rounds)}/{p.total_rounds})")

            penalty = min(1.0, flip_score * self.flip_penalty + max(0, cs - self.collusion_threshold) * 0.5)

            reports.append(ConsistencyReport(
                agent_index=i,
                flip_score=flip_score,
                collusion_score=cs,
                penalty=penalty,
                flags=flags,
            ))

        return reports

    def _detect_collusion(self, embeddings: np.ndarray) -> list[float]:
        """Compute max pairwise similarity for each agent (collusion indicator)."""
        n = embeddings.shape[0]
        if n < 2:
            return [0.0] * n

        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms < 1e-12, 1.0, norms)
        normed = embeddings / norms
        sim = normed @ normed.T
        np.fill_diagonal(sim, 0.0)
        return [float(sim[i].max()) for i in range(n)]

    @property
    def round_count(self) -> int:
        """Number of rounds recorded so far."""
        return self._round_count

    def reset(self) -> None:
        """Clear all accumulated profiles."""
        self.profiles = [AgentProfile() for _ in range(self.n_agents)]
        self._round_count = 0
