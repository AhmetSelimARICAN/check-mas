"""Tests for multi-round consistency tracking."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from checkmas.analysis.consistency import ConsistencyTracker


class TestConsistencyTracker:
    def test_basic_recording(self):
        ct = ConsistencyTracker(n_agents=3)
        reports = ct.record_round(
            responses=["A is true", "A is false", "A is false"],
            stances=["SUPPORTED", "REFUTED", "REFUTED"],
        )
        assert len(reports) == 3
        assert ct.round_count == 1

    def test_flip_detection(self):
        ct = ConsistencyTracker(n_agents=2)
        ct.record_round(
            responses=["A", "B"],
            stances=["SUPPORTED", "REFUTED"],
        )
        reports = ct.record_round(
            responses=["A changed", "B same"],
            stances=["REFUTED", "REFUTED"],
        )
        assert reports[0].flip_score > 0
        assert reports[1].flip_score == 0
        assert ct.profiles[0].flip_count == 1

    def test_collusion_detection(self):
        ct = ConsistencyTracker(n_agents=3, collusion_threshold=0.90)
        emb = np.array([
            [1.0, 0.0, 0.0],
            [0.99, 0.01, 0.0],
            [0.0, 1.0, 0.0],
        ])
        reports = ct.record_round(
            responses=["A", "almost A", "B"],
            stances=[None, None, None],
            embeddings=emb,
        )
        assert reports[0].collusion_score > 0.9
        assert reports[1].collusion_score > 0.9
        assert reports[2].collusion_score < 0.5

    def test_reset(self):
        ct = ConsistencyTracker(n_agents=2)
        ct.record_round(responses=["A", "B"], stances=["S", "R"])
        ct.reset()
        assert ct.round_count == 0

    def test_multi_round_penalty(self):
        ct = ConsistencyTracker(n_agents=2, flip_penalty=0.15)
        ct.record_round(responses=["A", "B"], stances=["SUPPORTED", "REFUTED"])
        ct.record_round(responses=["A", "B"], stances=["REFUTED", "REFUTED"])
        reports = ct.record_round(responses=["A", "B"], stances=["SUPPORTED", "REFUTED"])
        assert reports[0].penalty > 0
        assert reports[0].flip_score > 0

    def test_flagged_round_tracking(self):
        ct = ConsistencyTracker(n_agents=3)
        ct.record_round(
            responses=["A", "B", "C"],
            stances=[None, None, None],
            flagged_indices=[1, 2],
        )
        ct.record_round(
            responses=["A", "B", "C"],
            stances=[None, None, None],
            flagged_indices=[1],
        )
        assert len(ct.profiles[1].flagged_rounds) == 2
        assert len(ct.profiles[0].flagged_rounds) == 0
