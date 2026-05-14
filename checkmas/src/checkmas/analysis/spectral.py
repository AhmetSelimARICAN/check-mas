"""Spectral analysis — eigenvector centrality on agent similarity graphs."""

from __future__ import annotations

import numpy as np


def cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """Compute pairwise cosine similarity for row vectors.

    Parameters
    ----------
    embeddings : np.ndarray, shape (n, dim)

    Returns
    -------
    np.ndarray, shape (n, n)
        Values in [-1, 1].
    """
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    X = embeddings / norms
    return np.clip(X @ X.T, -1.0, 1.0)


def spectral_centrality(embeddings: np.ndarray) -> np.ndarray:
    """Eigenvector centrality from embedding similarity.

    Agents whose responses are semantically close to the group consensus
    receive higher centrality scores.

    Parameters
    ----------
    embeddings : np.ndarray, shape (n, dim)

    Returns
    -------
    np.ndarray, shape (n,)
        Non-negative, sums to 1.
    """
    n = embeddings.shape[0]
    if n == 0:
        return np.array([])
    W = cosine_similarity_matrix(embeddings)
    W_nonneg = np.maximum(W, 0.0)
    eigenvalues, eigenvectors = np.linalg.eigh(W_nonneg)
    u = np.abs(eigenvectors[:, np.argmax(eigenvalues)].real)
    s = u.sum()
    return u / s if s > 0 else np.ones(n) / n
