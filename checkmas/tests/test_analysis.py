"""Tests for spectral analysis and Bayesian trust update."""

import numpy as np
import pytest
from checkmas.analysis.spectral import cosine_similarity_matrix, spectral_centrality
from checkmas.analysis.bayesian import bayesian_update


class TestCosineSimilarity:
    def test_identity(self):
        X = np.eye(3, dtype=float)
        W = cosine_similarity_matrix(X)
        np.testing.assert_array_almost_equal(np.diag(W), [1, 1, 1])

    def test_orthogonal_vectors(self):
        X = np.eye(3, dtype=float)
        W = cosine_similarity_matrix(X)
        assert W[0, 1] == pytest.approx(0.0, abs=1e-6)

    def test_parallel_vectors(self):
        X = np.array([[1, 0], [2, 0]], dtype=float)
        W = cosine_similarity_matrix(X)
        assert W[0, 1] == pytest.approx(1.0, abs=1e-6)

    def test_zero_vector_handled(self):
        X = np.array([[1, 0], [0, 0]], dtype=float)
        W = cosine_similarity_matrix(X)
        assert not np.isnan(W).any()


class TestSpectralCentrality:
    def test_uniform_for_identical(self):
        X = np.ones((3, 4), dtype=float)
        u = spectral_centrality(X)
        assert len(u) == 3
        assert pytest.approx(u.sum(), abs=1e-6) == 1.0

    def test_empty(self):
        u = spectral_centrality(np.array([]).reshape(0, 4))
        assert len(u) == 0

    def test_outlier_gets_lower_centrality(self):
        rng = np.random.default_rng(42)
        base = rng.standard_normal(10)
        X = np.stack([
            base + rng.standard_normal(10) * 0.1,
            base + rng.standard_normal(10) * 0.1,
            -base,
        ])
        u = spectral_centrality(X)
        assert u[2] < u[0]
        assert u[2] < u[1]


class TestBayesianUpdate:
    def test_sums_to_one(self):
        trust = np.array([0.5, 0.3, 0.2])
        fusion = np.array([0.9, 0.1, 0.5])
        result = bayesian_update(trust, fusion)
        assert pytest.approx(result.sum(), abs=1e-6) == 1.0

    def test_higher_fusion_gets_more_trust(self):
        trust = np.array([0.5, 0.5])
        fusion = np.array([0.9, 0.1])
        result = bayesian_update(trust, fusion)
        assert result[0] > result[1]

    def test_zero_fusion_fallback(self):
        trust = np.array([0.5, 0.5])
        fusion = np.array([0.0, 0.0])
        result = bayesian_update(trust, fusion)
        assert pytest.approx(result.sum(), abs=1e-6) == 1.0

    def test_alpha_amplifies_difference(self):
        trust = np.array([0.5, 0.5])
        fusion = np.array([0.8, 0.2])
        mild = bayesian_update(trust, fusion, alpha=1.0)
        strong = bayesian_update(trust, fusion, alpha=3.0)
        gap_mild = abs(mild[0] - mild[1])
        gap_strong = abs(strong[0] - strong[1])
        assert gap_strong > gap_mild
