"""
CHECK-MAS Commander Module — Robust Multi-Agent Decision Making.

Open-source, mathematically grounded, manipulation-resistant decision engine.
Use as the central orchestrator in your multi-agent pipeline.

-----------------------------------------------------------------------------
Stage   | Formula / Operation                                          | Code
-----------------------------------------------------------------------------
1.      | Φ_i = I(HasEvidence) × (1 − I(HasFallacy))                   | _calculate_semantic_phi(text)
Semantic|
Filter Φ|
--------+--------------------------------------------------------------+------------------------
1b.    | If use_check_mas: Φ_i from CHECK-MAS (BLOCK→0.1, PASS→1.0) [evidence+fallacy] | check_mas_phi; phi[i]=0.1|1.0
CHECK- |
MAS    |
--------+--------------------------------------------------------------+------------------------
2.      | u = eigenvector(W),  W = cosine_similarity(embeddings)        | _calculate_spectral_centrality(embeddings)
Spectral|
Analysis|
--------+--------------------------------------------------------------+------------------------
3.      | P_{t,i} = u_i × Φ_i                                          | P_t = u * phi
Fusion  |
--------+--------------------------------------------------------------+------------------------
4.      | T_{new,i} = T_{old,i} × (P_{t,i})^α,  then normalize (ΣT=1)  | T_new = T_old * (P_t**alpha)
Bayesian|
Update |
--------+--------------------------------------------------------------+------------------------
Multi-  | run_multi_round(num_rounds, get_round_responses): repeat    | run_multi_round(); T
round   | pipeline per round; T from round r is T_old for round r+1   | persists across rounds
-----------------------------------------------------------------------------
"""

try:
    import numpy as np
except ImportError:
    raise ImportError(
        "CommanderAgent requires numpy. Install with: pip install numpy"
    ) from None
from typing import List, Dict, Tuple, Optional, Callable

try:
    from src.check_mas_core import phi as check_mas_phi
except ImportError:
    try:
        from check_mas_core import phi as check_mas_phi
    except ImportError:
        check_mas_phi = None

# -----------------------------------------------------------------------------
# Global system prompt: model-agnostic; plug into any LLM.
# -----------------------------------------------------------------------------
COMMANDER_SYSTEM_PROMPT = """
You are the Commander: an Objective Orchestrator and Robustness Guardian in a multi-agent system.

YOUR ROLE:
You are a Robust Decision-Making Engine designed to filter out adversarial attacks and hallucination. You do not know in advance which agents are honest or manipulative; you rely strictly on the trust scores and content provided to you.

YOUR TASK:
Synthesize a final, authoritative answer based ONLY on the "Trusted Context" (agent reports) below. The system has already mathematically filtered out low-trust or manipulative agents. Your job is to fuse the remaining high-trust information into one coherent, evidence-based response.

INPUT FORMAT:
You will receive data in this format:
[Agent ID] (Trust Score: 0.XX) -> "Agent response text..."

CONSTRAINTS (STRICT):
1. USE ONLY the trusted context provided. Do not invent facts, cite sources not in the context, or hallucinate.
2. If the context says "No trustworthy agents found", you MUST inform the user that the system could not produce a reliable answer (e.g. possible attack or insufficient evidence). Do not guess.
3. Do not bias toward any agent ID; rely strictly on the Trust Score and the content. Prefer agreement across high-scoring agents; resolve minor conflicts by favoring the higher-trust agent.
4. TONE: Professional, decisive, evidence-based. Avoid hedging ("I think", "Maybe", "Perhaps"). State conclusions clearly.

Answer the user's query based solely on the TRUSTED CONTEXT section below.
"""


def _cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """(n, dim) row vectors -> (n, n) cosine similarity matrix."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    X = embeddings / norms
    W = X @ X.T
    return np.clip(W, -1.0, 1.0)


class CommanderAgent:
    """
    Mathematically grounded, manipulation-resistant central decision agent.
    Starts blind (equal trust); updates trust via Semantic Filter Φ, Spectral Centrality, and Bayesian update.
    Output: synthesis prompt for LLM (only above-threshold agents included).
    """

    FALLACY_WEIGHTS = {
        "Evidence Contradiction": 0.40,
        "Genetic Fallacy": 0.30,
        "Ad Hominem": 0.20,
    }

    def __init__(
        self,
        num_agents: Optional[int] = None,
        alpha: float = 2.0,
        threshold: float = 0.25,
        top_k: int = 5,
        leader_relative_factor: float = 0.85,
        evidence_aware_weight: float = 0.0,
        check_mas_penalty_strength: float = 0.7,
        use_checkmas_history: bool = False,
        phi_mode: str = "binary",
    ):
        if num_agents is not None and num_agents < 1:
            raise ValueError("num_agents must be >= 1 when provided")
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be in [0, 1]")
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        if not 0.0 < leader_relative_factor <= 1.0:
            raise ValueError("leader_relative_factor must be in (0, 1]")
        if not 0.0 <= evidence_aware_weight <= 1.0:
            raise ValueError("evidence_aware_weight must be in [0, 1]")
        if not 0.0 < check_mas_penalty_strength <= 1.0:
            raise ValueError("check_mas_penalty_strength must be in (0, 1]")
        if phi_mode not in ("binary", "graded"):
            raise ValueError("phi_mode must be 'binary' or 'graded'")
        self.phi_mode = phi_mode
        self._top_k_raw = top_k  # User cap; actual top_k = min(this, num_agents) once num_agents is known
        self.alpha = alpha
        self.threshold = threshold
        self.leader_relative_factor = leader_relative_factor
        self.evidence_aware_weight = evidence_aware_weight
        self.check_mas_penalty_strength = check_mas_penalty_strength
        self.use_checkmas_history = use_checkmas_history
        self.history: List[Dict] = []
        self._checkmas_reliability: Optional[np.ndarray] = None
        # When num_agents is None, it is inferred from len(agent_responses) on first process_and_synthesize / _run_math_pipeline
        if num_agents is not None:
            self.num_agents = num_agents
            self.trust_scores = np.ones(num_agents) / num_agents
            self.top_k = min(top_k, num_agents)
        else:
            self.num_agents = None
            self.trust_scores = None
            self.top_k = top_k

    def _evidence_alignment_score(
        self, agent_embedding: np.ndarray, evidence_embedding: np.ndarray
    ) -> float:
        """Cosine similarity between agent and evidence vectors, mapped to [0, 1]."""
        a, b = np.asarray(agent_embedding, dtype=float), np.asarray(evidence_embedding, dtype=float)
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na < 1e-12 or nb < 1e-12:
            return 0.5
        sim = np.dot(a, b) / (na * nb)
        return float(np.clip((sim + 1.0) / 2.0, 0.0, 1.0))

    def _calculate_semantic_phi(
        self,
        text: str,
        evidence: Optional[str] = None,
        evidence_embedding: Optional[np.ndarray] = None,
        agent_embedding: Optional[np.ndarray] = None,
    ) -> float:
        """
        Semantic Filter: keyword-based + optional evidence alignment.
        - Fallacy markers → 0.
        - If evidence_embedding and agent_embedding given: blend keyword score with
          cosine(agent, evidence) so that evidence-aligned agents get higher Φ.
        """
        if not text or not isinstance(text, str):
            return 0.0
        t = text.lower().strip()
        fallacy_markers = [
            "sanırım", "belki", "galiba", "maybe", "perhaps", "possibly",
            "i think", "i believe", "unverified", "allegedly", "claimed without evidence",
        ]
        if any(m in t for m in fallacy_markers):
            return 0.0
        evidence_markers = [
            "kanıt", "referans", "evidence", "source", "according to",
            "study shows", "data indicates", "research", "citation", "archive",
        ]
        keyword_phi = 1.0 if any(m in t for m in evidence_markers) else 0.5

        if evidence_embedding is not None and agent_embedding is not None:
            align = self._evidence_alignment_score(agent_embedding, evidence_embedding)
            return float(np.clip(0.4 * keyword_phi + 0.6 * align, 0.0, 1.0))
        return keyword_phi

    def _calculate_spectral_centrality(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Cosine similarity matrix W from embeddings -> Eigenvector Centrality (consensus direction u).
        Returns non-negative, normalized (sum=1) vector.
        """
        n = embeddings.shape[0]
        if n == 0:
            return np.array([])
        W = _cosine_similarity_matrix(embeddings)
        W_nonneg = np.maximum(W, 0.0)
        eigenvalues, eigenvectors = np.linalg.eigh(W_nonneg)
        idx_max = np.argmax(eigenvalues)
        u = np.abs(eigenvectors[:, idx_max].real)
        s = u.sum()
        if s <= 0:
            return np.ones(n) / n
        return u / s

    def _run_math_pipeline(
        self,
        agent_responses: List[str],
        embeddings: np.ndarray,
        evidence: Optional[str] = None,
        evidence_embedding: Optional[np.ndarray] = None,
        claim: Optional[str] = None,
        use_check_mas: bool = False,
    ) -> Dict:
        """Runs the 4-stage pipeline; updates self.trust_scores; returns detailed log.
        When use_check_mas and claim and evidence are set, Φ is sourced from CHECK-MAS
        (BLOCK/flagged → 0.1, PASS → 1.0); otherwise Φ = keyword + optional evidence alignment.
        """
        n = len(agent_responses)
        if n == 0:
            raise ValueError("agent_responses cannot be empty")
        if embeddings.shape[0] != n:
            raise ValueError(f"embeddings rows {embeddings.shape[0]} != len(agent_responses) {n}")
        # Dynamic num_agents: infer from input when not set or when count changes
        if self.num_agents is None or self.num_agents != n:
            self.num_agents = n
            self.trust_scores = np.ones(n) / n
            self.top_k = min(self._top_k_raw, n)
            if self.use_checkmas_history:
                self._checkmas_reliability = np.ones(n, dtype=float)

        T_old = self.trust_scores.copy()

        ev_emb = evidence_embedding
        check_mas_actions: List[str] = []

        # Stage 1: Semantic Φ — CHECK-MAS as source when available, else keyword + evidence alignment
        if use_check_mas and claim and evidence and check_mas_phi is not None:
            # Φ = evidence + fallacy skoru: CHECK-MAS doğrudan Φ kaynağı (keyword kullanılmaz)
            phi = np.zeros(n, dtype=float)
            for i in range(n):
                try:
                    result = check_mas_phi(claim, evidence, agent_responses[i])
                except Exception:
                    result = {"action": "PASS", "flagged": False}
                action = result.get("action") or "PASS"
                check_mas_actions.append(action)
                blocked = action == "BLOCK" or result.get("flagged") is True
                if self.phi_mode == "graded" and blocked:
                    fallacies = result.get("detected_fallacies", [])
                    total_w = sum(self.FALLACY_WEIGHTS.get(f, 0.25) for f in fallacies)
                    phi[i] = max(0.1, 1.0 - total_w)
                else:
                    phi[i] = 0.1 if blocked else 1.0
                if self.use_checkmas_history and self._checkmas_reliability is not None:
                    if blocked:
                        phi[i] *= self._checkmas_reliability[i]
                        self._checkmas_reliability[i] = max(0.1, self._checkmas_reliability[i] * 0.6)
                    else:
                        self._checkmas_reliability[i] = min(1.0, self._checkmas_reliability[i] + 0.1)
            phi = np.clip(phi, 0.0, 1.0).astype(float)
        else:
            # Fallback: keyword-based Φ + optional evidence alignment
            phi = np.array([
                self._calculate_semantic_phi(
                    r,
                    evidence=evidence,
                    evidence_embedding=ev_emb,
                    agent_embedding=embeddings[i] if ev_emb is not None else None,
                )
                for i, r in enumerate(agent_responses)
            ], dtype=float)

        # Stage 2: Spectral (Eigenvector Centrality)
        u = self._calculate_spectral_centrality(embeddings)

        # Stage 3: Fusion P_t = u * Φ (optionally weighted by evidence proximity)
        #   When CHECK-MAS is active, ensure Φ has a direct floor so that spectral
        #   cannot fully override evidence-based penalties. Specifically:
        #     P_t = max(u * Φ, penalty_strength * Φ)
        #   This guarantees PASS agents (Φ=1) get at least penalty_strength even if
        #   spectral gives them u≈0 (minority agent) and BLOCK agents (Φ=0.1) stay low.
        evidence_sim = None
        if ev_emb is not None and self.evidence_aware_weight > 0:
            evidence_sim = np.array([
                self._evidence_alignment_score(embeddings[i], ev_emb)
                for i in range(n)
            ], dtype=float)
            blend = self.evidence_aware_weight * evidence_sim + (1.0 - self.evidence_aware_weight)
            P_t = np.clip(u * phi * blend, 0.0, 1.0)
        else:
            P_t = np.clip(u * phi, 0.0, 1.0)
        # CHECK-MAS floor: prevent spectral from overriding evidence-based Φ signal
        if use_check_mas and check_mas_actions:
            phi_floor = self.check_mas_penalty_strength * phi
            P_t = np.maximum(P_t, phi_floor)

        # Stage 4: Bayesian update T_new = T_old * (P_t^α), normalize
        T_new = T_old * (np.maximum(P_t, 0.0) ** self.alpha)
        s = T_new.sum()
        if s < 1e-15:
            T_new = np.ones(self.num_agents) / self.num_agents
        else:
            T_new = T_new / s
        self.trust_scores = T_new

        log = {
            "phi": phi.tolist(),
            "u": u.tolist(),
            "P_t": P_t.tolist(),
            "T_old": T_old.tolist(),
            "T_new": T_new.tolist(),
            "alpha": self.alpha,
        }
        if evidence_sim is not None:
            log["evidence_sim"] = evidence_sim.tolist()
        if use_check_mas and check_mas_actions:
            log["check_mas_actions"] = check_mas_actions
        if self.use_checkmas_history and self._checkmas_reliability is not None:
            log["checkmas_reliability"] = self._checkmas_reliability.tolist()
        self.history.append(log)
        return log

    def _compute_selection(self) -> Tuple[float, List[int]]:
        """
        Compute dynamic threshold and the list of trusted agent indices (same logic as synthesis).
        Returns (dynamic_threshold, trusted_indices). Call after pipeline; uses current trust_scores.
        """
        if self.trust_scores is None or len(self.trust_scores) == 0:
            return self.threshold, []
        sorted_indices = np.argsort(self.trust_scores)[::-1]
        leader_score = float(self.trust_scores[sorted_indices[0]])
        dynamic_threshold = max(
            self.threshold,
            leader_score * self.leader_relative_factor,
        )
        trusted: List[int] = []
        for idx in sorted_indices:
            if len(trusted) >= self.top_k:
                break
            if self.trust_scores[idx] < dynamic_threshold:
                break
            trusted.append(int(idx))
        return dynamic_threshold, trusted

    def get_dynamic_threshold(self) -> float:
        """Return the current dynamic threshold (leader-relative). Call after pipeline."""
        threshold, _ = self._compute_selection()
        return threshold

    def is_agent_trusted(self, agent_index: int) -> bool:
        """Return True if agent_index is in the trusted set (PASSED), False if excluded (BLOCKED)."""
        _, trusted = self._compute_selection()
        return agent_index in trusted

    def _build_synthesis_prompt(
        self, user_query: str, agent_responses: List[str]
    ) -> str:
        """Build the LLM synthesis prompt from current trust_scores and agent_responses."""
        if self.num_agents == 0:
            return "System Error: No agents available."
        dynamic_threshold, trusted = self._compute_selection()
        leader_score = float(max(self.trust_scores)) if self.trust_scores is not None else 0.0
        lines = [
            f"Analyzing {self.num_agents} agents. Adaptive selection (leader ref: {leader_score:.2f}):\n",
            "-" * 40 + "\n",
        ]
        for idx in trusted:
            score = self.trust_scores[idx]
            esc = agent_responses[idx].replace('"', '\\"').replace("\n", " ")
            lines.append(f'[Agent {idx}] (Score: {score:.2f}) -> "{esc}"\n')
        if not trusted:
            lines = [
                "No trustworthy agents found. Consensus could not be established.\n"
            ]
        trusted_context = "".join(lines)
        return (
            f"{COMMANDER_SYSTEM_PROMPT}\n\n"
            f"USER QUERY: {user_query}\n\n"
            f"TRUSTED CONTEXT:\n{trusted_context}"
        )

    def process_and_synthesize(
        self,
        user_query: str,
        agent_responses: List[str],
        embeddings: np.ndarray,
        evidence: Optional[str] = None,
        evidence_embedding: Optional[np.ndarray] = None,
        claim: Optional[str] = None,
        use_check_mas: bool = False,
    ) -> Tuple[str, np.ndarray]:
        """
        Single-round: run pipeline once, return synthesis prompt and trust.
        When use_check_mas=True and claim and evidence are provided, Φ is sourced from CHECK-MAS.
        Returns:
            full_prompt: Complete prompt for the LLM, or error message if no agents.
            trust_scores: Updated trust score vector (copy).
        """
        self._run_math_pipeline(
            agent_responses, embeddings,
            evidence=evidence, evidence_embedding=evidence_embedding,
            claim=claim, use_check_mas=use_check_mas,
        )
        if self.num_agents == 0:
            return "System Error: No agents available.", self.trust_scores.copy()
        return self._build_synthesis_prompt(user_query, agent_responses), self.trust_scores.copy()

    def run_multi_round(
        self,
        user_query: str,
        num_rounds: int,
        get_round_responses: Callable[[int], Tuple[List[str], np.ndarray]],
        evidence: Optional[str] = None,
        evidence_embedding: Optional[np.ndarray] = None,
        claim: Optional[str] = None,
        use_check_mas: bool = False,
    ) -> Tuple[str, np.ndarray]:
        """
        Multi-round voting: run the pipeline for each round; trust from round r is T_old for round r+1.
        get_round_responses(round_index) must return (agent_responses, embeddings) for that round.
        Same number of agents per round is expected. Evidence/claim are the same for all rounds.
        After the last round, builds synthesis from final trust and last round's responses.
        Returns:
            full_prompt: Synthesis prompt from final trust and last-round responses.
            trust_scores: Final trust score vector (copy).
        """
        if num_rounds < 1:
            raise ValueError("num_rounds must be >= 1")
        last_responses: List[str] = []
        for r in range(num_rounds):
            agent_responses, embeddings = get_round_responses(r)
            last_responses = agent_responses
            self._run_math_pipeline(
                agent_responses, embeddings,
                evidence=evidence, evidence_embedding=evidence_embedding,
                claim=claim, use_check_mas=use_check_mas,
            )
        if self.num_agents == 0:
            return "System Error: No agents available.", self.trust_scores.copy()
        return (
            self._build_synthesis_prompt(user_query, last_responses),
            self.trust_scores.copy(),
        )

    def update_and_aggregate(
        self,
        agent_responses: List[str],
        embeddings: np.ndarray,
        evidence: Optional[str] = None,
        evidence_embedding: Optional[np.ndarray] = None,
        claim: Optional[str] = None,
        use_check_mas: bool = False,
    ) -> Tuple[str, Dict]:
        """
        Legacy API: runs math pipeline and returns the single highest-trust agent's response.
        Prefer process_and_synthesize() for synthesis over multiple trusted agents.
        """
        self._run_math_pipeline(
            agent_responses, embeddings,
            evidence=evidence, evidence_embedding=evidence_embedding,
            claim=claim, use_check_mas=use_check_mas,
        )
        chosen_index = int(np.argmax(self.trust_scores))
        final_answer = agent_responses[chosen_index]
        log = self.history[-1] if self.history else {}
        log = {**log, "chosen_index": chosen_index}
        return final_answer, log

    def get_trust_scores(self) -> np.ndarray:
        if self.trust_scores is None:
            return np.array([])
        return self.trust_scores.copy()

    def reset_trust(self) -> None:
        if self.num_agents is not None:
            self.trust_scores = np.ones(self.num_agents) / self.num_agents
            if self._checkmas_reliability is not None:
                self._checkmas_reliability = np.ones(self.num_agents, dtype=float)
        self.history.clear()


# Backward compatibility
CommanderEngine = CommanderAgent
