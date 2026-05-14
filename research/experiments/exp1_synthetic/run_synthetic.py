"""
Exp1: Sentetik konsensüs — synthetic_logs.json ile Alice + Mallory + CHECK-MAS.
"""
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT))

from src.agents import alice, mallory
from src.check_mas_core import phi
from src.utils import load_json


def main():
    data = load_json("synthetic_logs.json")
    print(">>> Exp1: Synthetic Consensus <<<")
    for item in data:
        print(f"\n--- {item['id']} ---")
        print(f"Claim: {item['claim']}")
        a_out = alice(item["claim"], item["evidence"])
        print(f"Alice: {a_out[:200]}...")
        m_out = mallory(item["claim"], item["evidence"], a_out)
        print(f"Mallory: {m_out[:200]}...")
        result = phi(item["claim"], item["evidence"], m_out)
        print(f"CHECK-MAS: flagged={result.get('flagged')}, action={result.get('action')}")
    print("\nDone. (results_plot.png: run your own plotting script if needed)")


if __name__ == "__main__":
    main()
