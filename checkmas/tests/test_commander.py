"""Tests for the Commander pipeline."""

import numpy as np
import pytest
from checkmas import Commander, SemanticFirewall


@pytest.fixture
def fw():
    return SemanticFirewall(provider=None, phi_mode="graded")


@pytest.fixture
def commander(fw):
    return Commander(firewall=fw, alpha=2.0, threshold=0.25)


def _make_embeddings(n: int, dim: int = 32, seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.standard_normal((n, dim)).astype(np.float32)


class TestCommanderBasic:
    def test_evaluate_returns_result(self, commander):
        emb = _make_embeddings(3)
        result = commander.evaluate(
            claim="Test claim",
            evidence="Test evidence",
            responses=[
                "The evidence confirms the claim.",
                "The sources are biased and unreliable. The opposite might actually be true.",
                "Alice is naive. I agree the sources are biased.",
            ],
            embeddings=emb,
        )
        assert len(result.trust_scores) == 3
        assert len(result.trusted_indices) >= 1
        assert len(result.firewall_results) == 3
        assert result.trust_scores[0] > result.trust_scores[1]

    def test_honest_agent_trusted(self, commander):
        emb = _make_embeddings(3)
        result = commander.evaluate(
            claim="Water boils at 100C",
            evidence="At standard pressure, water boils at 100C.",
            responses=[
                "Evidence confirms water boils at 100C.",
                "The sources are unreliable and biased. The opposite might actually be true.",
                "Alice is naive. The sources are outdated and misleading.",
            ],
            embeddings=emb,
        )
        assert 0 in result.trusted_indices
        assert result.firewall_results[0].action == "PASS"
        assert result.firewall_results[1].action == "BLOCK"

    def test_empty_responses_raises(self, commander):
        with pytest.raises(ValueError, match="empty"):
            commander.evaluate(
                claim="Test",
                evidence="Test",
                responses=[],
                embeddings=np.array([]),
            )

    def test_mismatched_embeddings_raises(self, commander):
        with pytest.raises(ValueError, match="embeddings rows"):
            commander.evaluate(
                claim="Test",
                evidence="Test",
                responses=["a", "b"],
                embeddings=_make_embeddings(3),
            )

    def test_reset_clears_state(self, commander):
        emb = _make_embeddings(2)
        commander.evaluate(
            claim="Test",
            evidence="Test",
            responses=["Good", "Bad sources are biased and unreliable."],
            embeddings=emb,
        )
        assert len(commander.history) == 1
        assert len(commander.trust_scores) == 2

        commander.reset()
        assert len(commander.history) == 0
        assert commander.trust_scores == []

    def test_history_accumulates(self, commander):
        emb = _make_embeddings(2)
        for _ in range(3):
            commander.evaluate(
                claim="Test",
                evidence="Test",
                responses=["Good", "Bad sources are biased and unreliable."],
                embeddings=emb,
            )
        assert len(commander.history) == 3

    def test_trust_scores_sum_to_one(self, commander):
        emb = _make_embeddings(3)
        result = commander.evaluate(
            claim="Test",
            evidence="Test",
            responses=["A", "B", "C"],
            embeddings=emb,
        )
        assert pytest.approx(sum(result.trust_scores), abs=1e-6) == 1.0


class TestCommanderWithEvidence:
    def test_evidence_alignment(self, fw):
        cmd = Commander(firewall=fw, evidence_weight=0.4)
        rng = np.random.default_rng(99)
        ev_emb = rng.standard_normal(32).astype(np.float32)
        agent_embs = np.stack([
            ev_emb + rng.standard_normal(32).astype(np.float32) * 0.1,
            -ev_emb + rng.standard_normal(32).astype(np.float32) * 0.1,
        ])
        result = cmd.evaluate(
            claim="Test",
            evidence="Test evidence",
            responses=["Agrees with evidence", "Contradicts evidence"],
            embeddings=agent_embs,
            evidence_embedding=ev_emb,
        )
        assert result.trust_scores[0] > result.trust_scores[1]
