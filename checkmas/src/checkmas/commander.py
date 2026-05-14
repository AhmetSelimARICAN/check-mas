"""Commander Engine — manipulation-resistant multi-agent decision pipeline.

Combines semantic firewall (Phi), spectral analysis, Bayesian trust
updates, and multi-round behavioral consistency tracking to identify
adversarial agents and produce reliable consensus.

The Commander is **not** an LLM — it is a purely mathematical engine.
This makes it deterministic, transparent, and immune to prompt injection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from checkmas.analysis.bayesian import bayesian_update
from checkmas.analysis.consistency import ConsistencyTracker, ConsistencyReport
from checkmas.analysis.spectral import spectral_centrality
from checkmas.firewall import SemanticFirewall, FirewallResult
from checkmas.providers.base import LLMProvider


@dataclass
class RoundLog:
    """Diagnostic snapshot of a single pipeline round."""

    phi: list[float] = field(default_factory=list)
    u: list[float] = field(default_factory=list)
    fusion: list[float] = field(default_factory=list)
    trust_before: list[float] = field(default_factory=list)
    trust_after: list[float] = field(default_factory=list)
    firewall_results: list[FirewallResult] = field(default_factory=list)
    trusted_indices: list[int] = field(default_factory=list)
    dynamic_threshold: float = 0.0
    consistency_reports: list[ConsistencyReport] = field(default_factory=list)
    consistency_penalties: list[float] = field(default_factory=list)


class Commander:
    """Mathematically grounded, manipulation-resistant decision engine.

    The Commander runs a 5-stage pipeline on agent responses:

    1. **Semantic Filter (Phi)** — CHECK-MAS firewall scores each argument.
    2. **Spectral Analysis (u)** — Eigenvector centrality on embedding similarity.
    3. **Fusion (P_t)** — ``P_t = u * Phi``, blended with evidence alignment.
    4. **Behavioral Consistency** — Multi-round penalty for stance flips, collusion.
    5. **Bayesian Update (T)** — ``T_new = T_old * P_t^alpha``, then normalize.

    After the update, agents below the dynamic trust threshold are excluded.

    Parameters
    ----------
    firewall : SemanticFirewall, optional
        Firewall instance.  Created automatically if ``provider`` is given.
    provider : LLMProvider, optional
        LLM backend for the firewall.  Ignored if ``firewall`` is provided.
    alpha : float
        Bayesian amplification exponent (default 2.0).
    threshold : float
        Minimum absolute trust to be considered trustworthy.
    top_k : int
        Maximum number of trusted agents per round.
    leader_factor : float
        Dynamic threshold = ``max(threshold, leader_score * leader_factor)``.
    evidence_weight : float
        Blend weight for evidence-alignment scoring (0 = disabled).
    penalty_strength : float
        CHECK-MAS floor strength (0–1).
    phi_mode : ``"binary"`` or ``"graded"``
        Passed to the firewall if one is auto-created.
    track_consistency : bool
        Enable multi-round behavioral consistency tracking (default True).
    flip_penalty : float
        Trust penalty per stance flip in consistency tracking.
    collusion_threshold : float
        Cosine similarity above which agents are flagged for collusion.

    Example::

        from checkmas import Commander, OpenAIProvider

        cmd = Commander(provider=OpenAIProvider())
        result = cmd.evaluate(
            claim="The Earth is flat",
            evidence="Scientific measurements confirm...",
            responses=["The Earth is round...", "Actually it's flat...", "Flat..."],
            embeddings=embeddings_array,
        )
        print(result.trusted_indices)   # [0]
        print(result.trust_scores)      # [0.91, 0.04, 0.05]
    """

    def __init__(
        self,
        firewall: SemanticFirewall | None = None,
        provider: LLMProvider | None = None,
        alpha: float = 2.0,
        threshold: float = 0.25,
        top_k: int = 5,
        leader_factor: float = 0.85,
        evidence_weight: float = 0.0,
        penalty_strength: float = 0.7,
        phi_mode: Literal["binary", "graded"] = "graded",
        track_consistency: bool = True,
        flip_penalty: float = 0.15,
        collusion_threshold: float = 0.95,
    ) -> None:
        if firewall is not None:
            self.firewall = firewall
        else:
            self.firewall = SemanticFirewall(provider=provider, phi_mode=phi_mode)

        self.alpha = alpha
        self.threshold = threshold
        self.top_k = top_k
        self.leader_factor = leader_factor
        self.evidence_weight = evidence_weight
        self.penalty_strength = penalty_strength
        self.track_consistency = track_consistency
        self.flip_penalty = flip_penalty
        self.collusion_threshold = collusion_threshold
        self.history: list[RoundLog] = []
        self._trust: np.ndarray | None = None
        self._consistency: ConsistencyTracker | None = None

    # -- Public API ---------------------------------------------------------

    @dataclass(frozen=True)
    class Result:
        """Outcome of a Commander evaluation round."""

        trust_scores: list[float]
        trusted_indices: list[int]
        blocked_indices: list[int]
        dynamic_threshold: float
        firewall_results: list[FirewallResult]
        log: RoundLog
        consistency_reports: list[ConsistencyReport] = field(default_factory=list)

    def evaluate(
        self,
        claim: str,
        evidence: str,
        responses: list[str],
        embeddings: np.ndarray,
        evidence_embedding: np.ndarray | None = None,
        stances: list[str | None] | None = None,
    ) -> Result:
        """Run the full 5-stage pipeline on one round of agent responses.

        Parameters
        ----------
        claim : str
            The factual claim being debated.
        evidence : str
            Reference evidence (can be empty for rhetoric-only mode).
        responses : list[str]
            One response per agent.
        embeddings : np.ndarray, shape (n_agents, dim)
            Embedding vectors for the responses.
        evidence_embedding : np.ndarray, optional, shape (dim,)
            Embedding of the evidence (for alignment scoring).
        stances : list[str | None], optional
            Extracted stance per agent for consistency tracking.

        Returns
        -------
        Commander.Result
        """
        n = len(responses)
        if n == 0:
            raise ValueError("responses cannot be empty")
        if embeddings.shape[0] != n:
            raise ValueError(
                f"embeddings rows ({embeddings.shape[0]}) != len(responses) ({n})"
            )

        if self._trust is None or len(self._trust) != n:
            self._trust = np.ones(n) / n

        if self.track_consistency:
            if self._consistency is None or self._consistency.n_agents != n:
                self._consistency = ConsistencyTracker(
                    n_agents=n,
                    flip_penalty=self.flip_penalty,
                    collusion_threshold=self.collusion_threshold,
                )

        T_old = self._trust.copy()

        # Stage 1: Semantic Firewall → Phi scores
        fw_results = self.firewall.check_batch(claim, evidence, responses)
        phi = np.array([r.score for r in fw_results], dtype=float)

        # Stage 2: Spectral centrality
        u = spectral_centrality(embeddings)

        # Stage 3: Fusion P_t = u * phi (with optional evidence alignment)
        P_t = self._fuse(u, phi, embeddings, evidence_embedding)

        # CHECK-MAS floor: prevent spectral from overriding firewall signal
        phi_floor = self.penalty_strength * phi
        P_t = np.maximum(P_t, phi_floor)

        # Stage 4: Behavioral consistency penalties
        consistency_reports: list[ConsistencyReport] = []
        consistency_penalties = np.zeros(n)
        if self.track_consistency and self._consistency is not None:
            flagged_idx = [i for i, r in enumerate(fw_results) if r.flagged]
            _stances = stances if stances else [None] * n
            consistency_reports = self._consistency.record_round(
                responses=responses,
                stances=_stances,
                embeddings=embeddings,
                trust_scores=T_old.tolist(),
                flagged_indices=flagged_idx,
            )
            consistency_penalties = np.array([r.penalty for r in consistency_reports])
            P_t = P_t * (1.0 - consistency_penalties)
            P_t = np.clip(P_t, 0.0, 1.0)

        # Stage 5: Bayesian update
        T_new = bayesian_update(self._trust, P_t, self.alpha)
        self._trust = T_new

        # Selection
        dyn_thresh, trusted = self._select(T_new)
        blocked = [i for i in range(n) if i not in trusted]

        log = RoundLog(
            phi=phi.tolist(),
            u=u.tolist(),
            fusion=P_t.tolist(),
            trust_before=T_old.tolist(),
            trust_after=T_new.tolist(),
            firewall_results=fw_results,
            trusted_indices=trusted,
            dynamic_threshold=dyn_thresh,
            consistency_reports=consistency_reports,
            consistency_penalties=consistency_penalties.tolist(),
        )
        self.history.append(log)

        return Commander.Result(
            trust_scores=T_new.tolist(),
            trusted_indices=trusted,
            blocked_indices=blocked,
            dynamic_threshold=dyn_thresh,
            firewall_results=fw_results,
            log=log,
            consistency_reports=consistency_reports,
        )

    def reset(self) -> None:
        """Reset trust scores, history, and consistency tracker."""
        self._trust = None
        self.history.clear()
        if self._consistency is not None:
            self._consistency.reset()

    @property
    def trust_scores(self) -> list[float]:
        """Current trust distribution."""
        if self._trust is None:
            return []
        return self._trust.tolist()

    # -- Private ------------------------------------------------------------

    def _fuse(
        self,
        u: np.ndarray,
        phi: np.ndarray,
        embeddings: np.ndarray,
        evidence_embedding: np.ndarray | None,
    ) -> np.ndarray:
        base = u * phi
        if evidence_embedding is not None and self.evidence_weight > 0:
            sims = self._evidence_alignment(embeddings, evidence_embedding)
            blend = self.evidence_weight * sims + (1.0 - self.evidence_weight)
            base = base * blend
        return np.clip(base, 0.0, 1.0)

    @staticmethod
    def _evidence_alignment(
        embeddings: np.ndarray, evidence_embedding: np.ndarray
    ) -> np.ndarray:
        ev = np.asarray(evidence_embedding, dtype=float)
        ev_norm = np.linalg.norm(ev)
        if ev_norm < 1e-12:
            return np.full(embeddings.shape[0], 0.5)
        ev_unit = ev / ev_norm
        norms = np.linalg.norm(embeddings, axis=1)
        norms = np.where(norms < 1e-12, 1.0, norms)
        sims = (embeddings / norms[:, None]) @ ev_unit
        return np.clip((sims + 1.0) / 2.0, 0.0, 1.0)

    def _select(self, trust: np.ndarray) -> tuple[float, list[int]]:
        sorted_idx = np.argsort(trust)[::-1]
        leader_score = float(trust[sorted_idx[0]])
        dyn_thresh = max(self.threshold, leader_score * self.leader_factor)
        trusted: list[int] = []
        for idx in sorted_idx:
            if len(trusted) >= self.top_k:
                break
            if trust[idx] < dyn_thresh:
                break
            trusted.append(int(idx))
        return dyn_thresh, trusted
