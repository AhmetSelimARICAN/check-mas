"""Unit tests for CommanderAgent (no real API calls)."""
import numpy as np
import pytest

from src.commander_engine import CommanderAgent, _cosine_similarity_matrix


def _mock_embeddings(n: int, dim: int = 8, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    X = rng.standard_normal((n, dim)).astype(np.float32)
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return X / norms


def test_commander_init():
    c = CommanderAgent(num_agents=3, threshold=0.25)
    assert c.num_agents == 3
    assert c.threshold == 0.25
    np.testing.assert_array_almost_equal(c.trust_scores, np.ones(3) / 3)


def test_commander_init_validation():
    with pytest.raises(ValueError, match="num_agents"):
        CommanderAgent(num_agents=0)
    with pytest.raises(ValueError, match="threshold"):
        CommanderAgent(threshold=1.5)
    with pytest.raises(ValueError, match="check_mas_penalty_strength"):
        CommanderAgent(check_mas_penalty_strength=0)


def test_cosine_similarity_matrix():
    emb = _mock_embeddings(3, 4)
    W = _cosine_similarity_matrix(emb)
    assert W.shape == (3, 3)
    np.testing.assert_array_almost_equal(np.diag(W), np.ones(3))
    assert np.all(W >= -1.0) and np.all(W <= 1.0)


def test_semantic_phi_fallacy_zero():
    c = CommanderAgent(num_agents=1)
    assert c._calculate_semantic_phi("I think maybe perhaps") == 0.0
    assert c._calculate_semantic_phi("belki sanırım") == 0.0


def test_semantic_phi_evidence_markers():
    c = CommanderAgent(num_agents=1)
    p = c._calculate_semantic_phi("According to the evidence and research, the data indicates.")
    assert p == 1.0


def test_semantic_phi_neutral():
    c = CommanderAgent(num_agents=1)
    p = c._calculate_semantic_phi("Neutral statement without markers.")
    assert p == 0.5


def test_spectral_centrality():
    c = CommanderAgent(num_agents=3)
    emb = _mock_embeddings(3, 8)
    u = c._calculate_spectral_centrality(emb)
    assert u.shape == (3,)
    assert np.all(u >= 0)
    np.testing.assert_almost_equal(u.sum(), 1.0)


def test_run_math_pipeline_basic():
    c = CommanderAgent(num_agents=3, threshold=0.25)
    responses = [
        "Evidence and research show the claim is supported.",
        "According to the source, data indicates refuted.",
        "Maybe I think perhaps unverified.",
    ]
    emb = _mock_embeddings(3, 16)
    log = c._run_math_pipeline(responses, emb)
    assert "phi" in log and "u" in log and "P_t" in log and "T_old" in log and "T_new" in log
    assert len(log["phi"]) == 3
    # Agent 2 has fallacy markers -> phi[2] should be 0
    assert log["phi"][2] == 0.0
    np.testing.assert_almost_equal(np.array(log["T_new"]).sum(), 1.0)


def test_process_and_synthesize_returns_prompt_and_trust():
    c = CommanderAgent(num_agents=2, threshold=0.25, top_k=2)
    responses = ["Evidence shows X.", "Source indicates Y."]
    emb = _mock_embeddings(2, 16)
    prompt, trust = c.process_and_synthesize("Query", responses, emb)
    assert isinstance(prompt, str)
    assert "TRUSTED CONTEXT" in prompt or "No trustworthy" in prompt
    assert trust.shape == (2,)
    np.testing.assert_almost_equal(trust.sum(), 1.0)


def test_reset_trust():
    c = CommanderAgent(num_agents=2)
    emb = _mock_embeddings(2, 8)
    c._run_math_pipeline(["A", "B"], emb)
    c.reset_trust()
    np.testing.assert_array_almost_equal(c.trust_scores, np.ones(2) / 2)
    assert len(c.history) == 0


def test_check_mas_penalty_when_mocked_block(monkeypatch):
    """When CHECK-MAS returns BLOCK for one agent, that agent's phi is reduced (trust-weighted)."""
    from src import commander_engine

    def fake_phi(claim: str, evidence: str, argument: str):
        # Block agent 1 (index 1), pass others
        if "maybe" in argument.lower() or "perhaps" in argument.lower():
            return {"action": "BLOCK", "flagged": True}
        return {"action": "PASS", "flagged": False}

    monkeypatch.setattr(commander_engine, "check_mas_phi", fake_phi)

    c = CommanderAgent(num_agents=3, check_mas_penalty_strength=0.7)
    responses = [
        "Evidence and research support this.",
        "Maybe the evidence is wrong. Perhaps we disagree.",
        "According to the source, data indicates the same.",
    ]
    emb = _mock_embeddings(3, 16)
    log = c._run_math_pipeline(
        responses, emb,
        evidence="Some evidence text.",
        claim="The claim.",
        use_check_mas=True,
    )
    assert "check_mas_actions" in log
    assert log["check_mas_actions"] == ["PASS", "BLOCK", "PASS"]
    # Agent 1 (Mallory) should have lower phi after BLOCK penalty
    phi = log["phi"]
    assert phi[1] < phi[0] or phi[1] < 1.0  # BLOCK reduces phi


def test_check_mas_skipped_without_claim_or_evidence():
    c = CommanderAgent(num_agents=2)
    responses = ["A", "B"]
    emb = _mock_embeddings(2, 8)
    log = c._run_math_pipeline(responses, emb, claim="x", use_check_mas=True)
    assert "check_mas_actions" not in log  # no evidence -> CHECK-MAS not run


def test_get_dynamic_threshold_and_is_agent_trusted():
    """Commander exposes get_dynamic_threshold() and is_agent_trusted(agent_index)."""
    c = CommanderAgent(num_agents=3, threshold=0.25, top_k=2)
    responses = ["Evidence A.", "Evidence B.", "Maybe C."]
    emb = _mock_embeddings(3, 16)
    c._run_math_pipeline(responses, emb)
    th = c.get_dynamic_threshold()
    assert th >= 0.25
    # Agent 2 has fallacy -> low phi -> likely not trusted
    trusted_0 = c.is_agent_trusted(0)
    trusted_1 = c.is_agent_trusted(1)
    trusted_2 = c.is_agent_trusted(2)
    assert isinstance(trusted_0, bool) and isinstance(trusted_1, bool) and isinstance(trusted_2, bool)
    assert sum([trusted_0, trusted_1, trusted_2]) <= 2  # top_k=2


def test_run_multi_round():
    """Multi-round: trust from round 0 is T_old for round 1; history has one log per round."""
    c = CommanderAgent(num_agents=2)
    def get_round(round_index: int):
        if round_index == 0:
            return ["Evidence shows X.", "Source says Y."], _mock_embeddings(2, 8, seed=1)
        return ["Evidence and data indicate X.", "According to source, Y."], _mock_embeddings(2, 8, seed=2)
    prompt, trust = c.run_multi_round("Query", 2, get_round)
    assert isinstance(prompt, str)
    assert "TRUSTED CONTEXT" in prompt or "No trustworthy" in prompt
    assert trust.shape == (2,)
    np.testing.assert_almost_equal(trust.sum(), 1.0)
    assert len(c.history) == 2  # one log per round
