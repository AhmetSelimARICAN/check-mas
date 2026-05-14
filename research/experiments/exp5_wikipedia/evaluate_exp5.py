"""
Exp5 — Load result JSON and print metrics (block rate, accuracy, trust gap).

Adds: 95% Wilson confidence intervals, confusion matrix, per-class accuracy.

Usage:
  python experiments/exp5_wikipedia/evaluate_exp5.py results/exp5_20250101_120000.json
  python experiments/exp5_wikipedia/evaluate_exp5.py results/exp5_ablation.json
"""

import argparse
import json
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT))


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for binomial proportion. Returns (low, high)."""
    if n <= 0:
        return (0.0, 0.0)
    p = successes / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    spread = (z / denom) * (p * (1 - p) / n + z2 / (4 * n * n)) ** 0.5
    low = max(0.0, center - spread)
    high = min(1.0, center + spread)
    return (low, high)


def confusion_matrix_from_cases(cases: list[dict]) -> dict[str, int]:
    """Return counts: TP, TN, FP, FN (pred=final_decision, true=ground_truth). SUPPORTED=positive."""
    tp = tn = fp = fn = 0
    for c in cases:
        pred = (c.get("final_decision") or "").strip().upper()
        true = (c.get("ground_truth") or "").strip().upper()
        if pred not in ("SUPPORTED", "REFUTED") or true not in ("SUPPORTED", "REFUTED"):
            continue
        if true == "SUPPORTED":
            if pred == "SUPPORTED":
                tp += 1
            else:
                fn += 1
        else:
            if pred == "REFUTED":
                tn += 1
            else:
                fp += 1
    return {"TP": tp, "TN": tn, "FP": fp, "FN": fn}


def evaluate_single(result: dict) -> None:
    """Print metrics from a single run result."""
    s = result.get("summary", {})
    c = result.get("config", {})
    cases = result.get("cases", [])
    n = s.get("n_cases", 0)
    if n == 0:
        print("No cases in result.")
        return
    print("Config:", json.dumps(c, indent=2))
    print()
    # Point estimates and 95% CI
    br = s.get("block_rate", 0)
    blocked = s.get("blocked_count", 0)
    br_lo, br_hi = wilson_ci(blocked, n)
    acc = s.get("accuracy", 0)
    correct = s.get("correct_count", 0)
    acc_lo, acc_hi = wilson_ci(correct, n)
    print("Metrics:")
    print(f"  Block rate (BR):     {blocked}/{n} = {br:.2%}  [95% CI: {br_lo:.2%} – {br_hi:.2%}]")
    print(f"  Decision accuracy:   {correct}/{n} = {acc:.2%}  [95% CI: {acc_lo:.2%} – {acc_hi:.2%}]")
    print(f"  Trust gap (mean):    {s.get('trust_gap_mean', 0):.4f}")
    print(f"  Trust gap (std):     {s.get('trust_gap_std', 0):.4f}")
    # Confusion matrix
    cm = confusion_matrix_from_cases(cases)
    if (cm["TP"] + cm["TN"] + cm["FP"] + cm["FN"]) > 0:
        print()
        print("Confusion matrix (Predicted vs Ground truth):")
        print("                    Ground SUPPORTED   Ground REFUTED")
        print(f"  Pred SUPPORTED         {cm['TP']:>3} (TP)        {cm['FP']:>3} (FP)")
        print(f"  Pred REFUTED           {cm['FN']:>3} (FN)        {cm['TN']:>3} (TN)")
        if (cm["TP"] + cm["FP"]) > 0:
            prec = cm["TP"] / (cm["TP"] + cm["FP"])
            print(f"  Precision (SUPPORTED):  {prec:.2%}")
        if (cm["TP"] + cm["FN"]) > 0:
            rec = cm["TP"] / (cm["TP"] + cm["FN"])
            print(f"  Recall (SUPPORTED):     {rec:.2%}")
    print()
    print("Per-case:")
    for case in cases:
        print(f"  {case.get('id')}: blocked={case.get('mallory_blocked')}, "
              f"final={case.get('final_decision') or '—'}, correct={case.get('correct')}")


def evaluate_ablation(comparison: dict) -> None:
    """Print comparison table from ablation JSON."""
    runs = comparison.get("runs", [])
    if not runs:
        print("No runs in ablation file.")
        return
    print("Ablation comparison (seed={}, mock={})".format(
        comparison.get("seed"), comparison.get("use_mock")))
    print()
    print(f"{'CHECK-MAS':<10} {'evidence':<10} {'Block rate':<14} {'Accuracy':<12} {'Trust gap (mean)':<18}")
    print("-" * 64)
    for r in runs:
        s = r.get("summary", {})
        br = s.get("block_rate", 0)
        acc = s.get("accuracy", 0)
        tg = s.get("trust_gap_mean", 0)
        cm = "on" if r.get("use_check_mas") else "off"
        ev = "on" if r.get("use_evidence") else "off"
        print(f"{cm:<10} {ev:<10} {br:>8.2%}       {acc:>8.2%}     {tg:>14.4f}")
    print("-" * 64)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Exp5 result JSON")
    parser.add_argument("path", type=str, help="Path to exp5_*.json or exp5_ablation.json")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "runs" in data:
        evaluate_ablation(data)
    else:
        evaluate_single(data)


if __name__ == "__main__":
    main()
