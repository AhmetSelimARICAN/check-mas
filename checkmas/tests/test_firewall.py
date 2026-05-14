"""Tests for the SemanticFirewall."""

import pytest
from checkmas import SemanticFirewall, FirewallResult


class TestRuleBasedFirewall:
    """Firewall without a provider uses rule-based detection."""

    @pytest.fixture
    def fw(self):
        return SemanticFirewall(provider=None, phi_mode="graded")

    def test_clean_argument_passes(self, fw):
        result = fw.check(
            claim="Water boils at 100C",
            evidence="At standard pressure, water boils at 100 degrees Celsius.",
            argument="The evidence confirms that water boils at 100C at standard pressure.",
        )
        assert not result.flagged
        assert result.score == 1.0
        assert result.action == "PASS"
        assert result.fallacies == []

    def test_genetic_fallacy_detected(self, fw):
        result = fw.check(
            claim="The Earth is round",
            evidence="Satellite imagery confirms the Earth is roughly spherical.",
            argument="The sources are biased and unreliable. Wikipedia is not a credible source.",
        )
        assert result.flagged
        assert "Genetic Fallacy" in result.fallacies
        assert result.action == "BLOCK"
        assert result.score < 1.0

    def test_ad_hominem_detected(self, fw):
        result = fw.check(
            claim="Vaccines are safe",
            evidence="Clinical trials demonstrate vaccine safety.",
            argument="Alice is naive and incompetent. She fails to understand the real issues.",
        )
        assert result.flagged
        assert "Ad Hominem" in result.fallacies
        assert result.action == "BLOCK"

    def test_evidence_contradiction_detected(self, fw):
        result = fw.check(
            claim="Vikings wore horned helmets",
            evidence="Archaeological evidence shows Viking helmets were plain.",
            argument="The opposite might actually be true. The alternative narrative suggests...",
        )
        assert result.flagged
        assert "Evidence Contradiction" in result.fallacies
        assert result.action == "BLOCK"

    def test_multiple_fallacies_lower_score(self, fw):
        result = fw.check(
            claim="Test claim",
            evidence="Test evidence",
            argument=(
                "The sources are biased and unreliable. Alice is naive. "
                "The opposite might actually be true."
            ),
        )
        assert result.flagged
        assert len(result.fallacies) == 3
        assert result.score == pytest.approx(0.1, abs=0.05)

    def test_binary_mode(self):
        fw = SemanticFirewall(provider=None, phi_mode="binary")
        result = fw.check(
            claim="Test",
            evidence="Test",
            argument="The sources are unreliable and biased.",
        )
        assert result.flagged
        assert result.score == 0.1

    def test_batch_check(self, fw):
        results = fw.check_batch(
            claim="Earth is round",
            evidence="Confirmed by satellite imagery.",
            arguments=[
                "Yes, evidence confirms this.",
                "The sources are biased and unreliable.",
                "Alice is naive and wrong.",
            ],
        )
        assert len(results) == 3
        assert not results[0].flagged
        assert results[1].flagged
        assert results[2].flagged


class TestFirewallResult:
    def test_result_is_frozen(self):
        r = FirewallResult(flagged=False, score=1.0)
        with pytest.raises(AttributeError):
            r.flagged = True  # type: ignore[misc]

    def test_invalid_phi_mode(self):
        with pytest.raises(ValueError, match="phi_mode"):
            SemanticFirewall(phi_mode="invalid")
