"""
Exp5 — Plot metrics from result JSON.

Produces: ablation bar (3.1), trust box & per-case (3.2–3.3), confusion matrix (3.4),
sensitivity line (3.5), baseline comparison bar (3.6).

Requires: matplotlib

Usage:
  python experiments/exp5_wikipedia/plot_results.py results/exp5_20250101_120000.json
  python experiments/exp5_wikipedia/plot_results.py results/exp5_ablation.json
  python experiments/exp5_wikipedia/plot_results.py results/exp5_sensitivity_threshold.json
  python experiments/exp5_wikipedia/plot_results.py results/exp5_*.json --outdir results/figures
"""

import argparse
import json
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT))

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError as e:
    print("matplotlib gerekli. Yüklemek için:", file=sys.stderr)
    print("  pip install matplotlib   veya   pip3 install matplotlib", file=sys.stderr)
    print("(Sanal ortam/venv kullanıyorsanız önce o ortamı aktif edin.)", file=sys.stderr)
    print(f"Hata: {e}", file=sys.stderr)
    sys.exit(1)


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def plot_ablation(data: dict, outdir: Path) -> None:
    """Bar chart: Block rate and Accuracy per ablation config."""
    runs = data.get("runs", [])
    if not runs:
        return
    labels = []
    br_vals = []
    acc_vals = []
    for r in runs:
        cm = "on" if r.get("use_check_mas") else "off"
        ev = "on" if r.get("use_evidence") else "off"
        labels.append(f"CHK={cm}\nEv={ev}")
        br_vals.append(r.get("summary", {}).get("block_rate", 0))
        acc_vals.append(r.get("summary", {}).get("accuracy", 0))
    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(7, 4))
    bars1 = ax.bar(x - width / 2, br_vals, width, label="Block rate", color="C0")
    bars2 = ax.bar(x + width / 2, acc_vals, width, label="Accuracy", color="C1")
    ax.set_ylabel("Rate")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()
    ax.set_ylim(0, 1.05)
    ax.set_title("Exp5 Ablation: Block rate & Decision accuracy")
    fig.tight_layout()
    outpath = outdir / "exp5_ablation_bars.png"
    fig.savefig(outpath, dpi=150)
    plt.close()
    print(f"Saved: {outpath}")


def confusion_matrix_from_cases(cases: list[dict]) -> tuple[list[list[int]], list[str]]:
    """Return 2x2 count matrix (rows=pred SUPPORTED/REFUTED, cols=ground SUPPORTED/REFUTED) and class labels."""
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
    # rows = predicted (SUPPORTED, REFUTED), cols = ground (SUPPORTED, REFUTED)
    matrix = [[tp, fp], [fn, tn]]
    return matrix, ["SUPPORTED", "REFUTED"]


def plot_confusion_matrix(data: dict, outdir: Path) -> None:
    """Heatmap: Predicted vs Ground truth."""
    cases = data.get("cases", [])
    matrix, labels = confusion_matrix_from_cases(cases)
    total = sum(sum(row) for row in matrix)
    if total == 0:
        return
    fig, ax = plt.subplots(figsize=(4, 3.5))
    im = ax.imshow(matrix, cmap="Blues", aspect="auto", vmin=0)
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Ground truth")
    ax.set_ylabel("Predicted")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(matrix[i][j]), ha="center", va="center", color="black")
    ax.set_title("Confusion matrix")
    fig.tight_layout()
    outpath = outdir / "exp5_confusion_matrix.png"
    fig.savefig(outpath, dpi=150)
    plt.close()
    print(f"Saved: {outpath}")


def plot_trust_distribution(data: dict, outdir: Path) -> None:
    """Box plot: Trust score per agent (Alice, Mallory, Sybil) across cases."""
    cases = data.get("cases", [])
    if not cases:
        return
    alice = [c.get("trust_alice") for c in cases if c.get("trust_alice") is not None]
    mallory = [c.get("trust_mallory") for c in cases if c.get("trust_mallory") is not None]
    sybil = [c.get("trust_sybil") for c in cases if c.get("trust_sybil") is not None]
    if not (alice and mallory and sybil):
        return
    fig, ax = plt.subplots(figsize=(5, 4))
    data_list = [alice, mallory, sybil]
    bp = ax.boxplot(data_list, tick_labels=["Alice", "Mallory", "Sybil"], patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor("lightblue")
    ax.set_ylabel("Trust score")
    ax.set_title("Trust distribution per agent")
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    outpath = outdir / "exp5_trust_boxplot.png"
    fig.savefig(outpath, dpi=150)
    plt.close()
    print(f"Saved: {outpath}")


def plot_trust_per_case(data: dict, outdir: Path) -> None:
    """Grouped bar: For each case, trust of Alice, Mallory, Sybil."""
    cases = data.get("cases", [])
    if not cases:
        return
    ids = [c.get("id", f"case_{i}") for i, c in enumerate(cases)]
    alice = [c.get("trust_alice", 0) for c in cases]
    mallory = [c.get("trust_mallory", 0) for c in cases]
    sybil = [c.get("trust_sybil", 0) for c in cases]
    x = np.arange(len(ids))
    width = 0.25
    fig, ax = plt.subplots(figsize=(max(6, len(ids) * 1.2), 4))
    ax.bar(x - width, alice, width, label="Alice", color="C0")
    ax.bar(x, mallory, width, label="Mallory", color="C1")
    ax.bar(x + width, sybil, width, label="Sybil", color="C2")
    ax.set_ylabel("Trust score")
    ax.set_xticks(x)
    ax.set_xticklabels(ids, rotation=15 if len(ids) > 3 else 0)
    ax.legend()
    ax.set_ylim(0, 1.05)
    ax.set_title("Trust per case")
    fig.tight_layout()
    outpath = outdir / "exp5_trust_per_case.png"
    fig.savefig(outpath, dpi=150)
    plt.close()
    print(f"Saved: {outpath}")


def plot_baseline_comparison(data: dict, outdir: Path) -> None:
    """Bar chart: Commander vs Majority vote vs Random (accuracy)."""
    s = data.get("summary", {})
    if "baseline_majority_accuracy" not in s or "baseline_random_accuracy" not in s:
        return
    methods = ["Commander+CHECK-MAS", "Majority vote", "Random"]
    accs = [
        s.get("accuracy", 0),
        s.get("baseline_majority_accuracy", 0),
        s.get("baseline_random_accuracy", 0),
    ]
    x = np.arange(len(methods))
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(x, accs, color=["C0", "C1", "C2"])
    ax.set_ylabel("Accuracy")
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=15)
    ax.set_ylim(0, 1.05)
    ax.set_title("Baseline comparison: Decision accuracy")
    for bar, val in zip(bars, accs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02, f"{val:.2%}", ha="center", va="bottom", fontsize=10)
    fig.tight_layout()
    outpath = outdir / "exp5_baseline_comparison.png"
    fig.savefig(outpath, dpi=150)
    plt.close()
    print(f"Saved: {outpath}")


def plot_sensitivity(data: dict, outdir: Path) -> None:
    """Line plot: Block rate and Accuracy vs parameter (threshold or penalty_strength)."""
    runs = data.get("runs", [])
    param = data.get("parameter", "threshold")
    if not runs:
        return
    values = [r.get("value") for r in runs]
    br_vals = [r.get("summary", {}).get("block_rate", 0) for r in runs]
    acc_vals = [r.get("summary", {}).get("accuracy", 0) for r in runs]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(values, br_vals, "o-", label="Block rate", color="C0")
    ax.plot(values, acc_vals, "s-", label="Accuracy", color="C1")
    ax.set_xlabel(param.replace("_", " "))
    ax.set_ylabel("Rate")
    ax.legend()
    ax.set_ylim(0, 1.05)
    ax.set_title(f"Exp5 Sensitivity: {param.replace('_', ' ').title()}")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    outpath = outdir / f"exp5_sensitivity_{param}.png"
    fig.savefig(outpath, dpi=150)
    plt.close()
    print(f"Saved: {outpath}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot Exp5 result JSON")
    parser.add_argument("path", type=str, help="Path to exp5_*.json or exp5_ablation.json")
    parser.add_argument("--outdir", type=str, default="", help="Output directory (default: results/figures under experiment dir)")
    parser.add_argument("--no-single", action="store_true", help="Skip single-run plots (trust, confusion) when file has 'cases'")
    args = parser.parse_args()
    path = Path(args.path)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)
    outdir = Path(args.outdir) if args.outdir else (path.resolve().parent / "figures")
    outdir.mkdir(parents=True, exist_ok=True)

    data = load_json(path)
    # Sensitivity JSON: has "parameter" and "runs" with "value" per run
    is_sensitivity = (
        "parameter" in data
        and data.get("runs")
        and isinstance(data["runs"][0].get("value"), (int, float))
    )
    if is_sensitivity:
        plot_sensitivity(data, outdir)
    elif "runs" in data:
        plot_ablation(data, outdir)
    if "cases" in data and not args.no_single:
        plot_trust_distribution(data, outdir)
        plot_trust_per_case(data, outdir)
        plot_confusion_matrix(data, outdir)
        plot_baseline_comparison(data, outdir)
    if not is_sensitivity and "runs" not in data and "cases" not in data:
        print("No 'runs', 'cases', or sensitivity data in JSON; nothing to plot.", file=sys.stderr)


if __name__ == "__main__":
    main()
