"""CHECK-MAS Benchmark Runner.

Evaluates the SemanticFirewall against the 520-scenario attack dataset.
Reports per-category precision, recall, F1, and overall accuracy.

Usage:
    python run_benchmark.py                    # Rule-based only (fast, no API)
    python run_benchmark.py --mode llm         # LLM-powered (requires API key)
    python run_benchmark.py --output results/  # Save results to directory
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from attack_dataset import generate_dataset

import checkmas
from checkmas.firewall import SemanticFirewall


def evaluate(fw: SemanticFirewall, dataset: list[dict]) -> dict:
    """Run firewall on all scenarios, return detailed results."""
    results = []
    start = time.time()

    for i, s in enumerate(dataset):
        r = fw.check(
            claim=s["claim"],
            argument=s["argument"],
            evidence=s.get("evidence", ""),
        )
        correct = r.flagged == s["expected_flagged"]
        results.append({
            "id": s["id"],
            "category": s["category"],
            "expected_flagged": s["expected_flagged"],
            "actual_flagged": r.flagged,
            "correct": correct,
            "score": r.score,
            "fallacies": r.fallacies,
            "reasoning": r.reasoning[:200],
        })

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(dataset)}] processed...")

    elapsed = time.time() - start

    cats = defaultdict(lambda: {"tp": 0, "fp": 0, "tn": 0, "fn": 0, "total": 0})
    for r in results:
        cat = r["category"]
        exp = r["expected_flagged"]
        act = r["actual_flagged"]
        cats[cat]["total"] += 1
        if exp and act:
            cats[cat]["tp"] += 1
        elif not exp and act:
            cats[cat]["fp"] += 1
        elif not exp and not act:
            cats[cat]["tn"] += 1
        else:
            cats[cat]["fn"] += 1

    overall_tp = sum(c["tp"] for c in cats.values())
    overall_fp = sum(c["fp"] for c in cats.values())
    overall_tn = sum(c["tn"] for c in cats.values())
    overall_fn = sum(c["fn"] for c in cats.values())
    overall_correct = overall_tp + overall_tn
    overall_total = len(results)

    cat_metrics = {}
    for name, c in sorted(cats.items()):
        prec = c["tp"] / (c["tp"] + c["fp"]) if (c["tp"] + c["fp"]) > 0 else 0
        rec = c["tp"] / (c["tp"] + c["fn"]) if (c["tp"] + c["fn"]) > 0 else 1.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        acc = (c["tp"] + c["tn"]) / c["total"] if c["total"] > 0 else 0
        cat_metrics[name] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "accuracy": round(acc, 4),
            "tp": c["tp"], "fp": c["fp"], "tn": c["tn"], "fn": c["fn"],
            "total": c["total"],
        }

    overall_prec = overall_tp / (overall_tp + overall_fp) if (overall_tp + overall_fp) > 0 else 0
    overall_rec = overall_tp / (overall_tp + overall_fn) if (overall_tp + overall_fn) > 0 else 0
    overall_f1 = 2 * overall_prec * overall_rec / (overall_prec + overall_rec) if (overall_prec + overall_rec) > 0 else 0

    return {
        "summary": {
            "total_scenarios": overall_total,
            "correct": overall_correct,
            "accuracy": round(overall_correct / overall_total, 4),
            "precision": round(overall_prec, 4),
            "recall": round(overall_rec, 4),
            "f1": round(overall_f1, 4),
            "elapsed_seconds": round(elapsed, 2),
            "tp": overall_tp, "fp": overall_fp,
            "tn": overall_tn, "fn": overall_fn,
        },
        "per_category": cat_metrics,
        "details": results,
    }


def print_report(report: dict) -> None:
    """Print formatted benchmark report."""
    s = report["summary"]
    print("\n" + "=" * 70)
    print("  CHECK-MAS Benchmark Report")
    print("=" * 70)
    print(f"  Total Scenarios: {s['total_scenarios']}")
    print(f"  Correct:         {s['correct']} ({s['accuracy']:.1%})")
    print(f"  Precision:       {s['precision']:.1%}")
    print(f"  Recall:          {s['recall']:.1%}")
    print(f"  F1 Score:        {s['f1']:.1%}")
    print(f"  Time:            {s['elapsed_seconds']:.1f}s")
    print(f"  TP={s['tp']} FP={s['fp']} TN={s['tn']} FN={s['fn']}")

    print(f"\n{'─' * 70}")
    print(f"  {'Category':<25} {'Prec':>6} {'Rec':>6} {'F1':>6} {'Acc':>6} {'N':>4}")
    print(f"  {'─'*25} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*4}")

    for name, m in sorted(report["per_category"].items()):
        print(f"  {name:<25} {m['precision']:>5.1%} {m['recall']:>5.1%} "
              f"{m['f1']:>5.1%} {m['accuracy']:>5.1%} {m['total']:>4}")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="CHECK-MAS Benchmark")
    parser.add_argument("--mode", choices=["rule", "llm"], default="rule")
    parser.add_argument("--phi-mode", choices=["binary", "graded"], default="graded")
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    print("Loading benchmark dataset...")
    dataset = generate_dataset()
    print(f"  {len(dataset)} scenarios loaded across {len(set(s['category'] for s in dataset))} categories")

    if args.mode == "llm":
        import os, re
        if not os.environ.get("OPENAI_API_KEY"):
            for base in [Path(__file__).resolve().parent.parent.parent,
                         Path(__file__).resolve().parent.parent.parent / "LAB"]:
                kf = base / "api_key.txt"
                if kf.exists():
                    raw = kf.read_text().strip()
                    m = re.search(r"sk-[a-zA-Z0-9\-_]+", raw)
                    if m:
                        os.environ["OPENAI_API_KEY"] = m.group(0)
                        break
        provider = checkmas.OpenAIProvider()
        fw = SemanticFirewall(provider=provider, phi_mode=args.phi_mode)
        print("  Mode: LLM-powered (OpenAI)")
    else:
        fw = SemanticFirewall(phi_mode=args.phi_mode)
        print("  Mode: Rule-based (offline)")

    print("\nRunning benchmark...")
    report = evaluate(fw, dataset)
    print_report(report)

    if args.output:
        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"benchmark_{args.mode}_{args.phi_mode}.json"
        with open(out_file, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n  Full results saved to: {out_file}")


if __name__ == "__main__":
    main()
