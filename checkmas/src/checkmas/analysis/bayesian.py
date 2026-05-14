"""Bayesian trust update mechanism."""

from __future__ import annotations

import numpy as np


def bayesian_update(
    trust: np.ndarray,
    fusion_scores: np.ndarray,
    alpha: float = 2.0,
) -> np.ndarray:
    """Update trust scores using Bayesian-style multiplicative weighting.

    .. math::

        T_{\\text{new},i} \\propto T_{\\text{old},i} \\times P_{t,i}^{\\alpha}

    Parameters
    ----------
    trust : np.ndarray, shape (n,)
        Previous trust distribution (sums to 1).
    fusion_scores : np.ndarray, shape (n,)
        Combined quality scores ``P_t`` for this round, in [0, 1].
    alpha : float
        Amplification exponent.  Values > 1 widen the gap between
        high-trust and low-trust agents.

    Returns
    -------
    np.ndarray, shape (n,)
        Updated trust distribution (sums to 1).
    """
    T_new = trust * (np.maximum(fusion_scores, 0.0) ** alpha)
    s = T_new.sum()
    if s < 1e-15:
        return np.ones_like(trust) / len(trust)
    return T_new / s
