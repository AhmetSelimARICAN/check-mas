"""
Exp4: Ölçeklenebilirlik ve dayanıklılık — daha fazla örnek / daha uzun kanıt ile test.
"""
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT))

from src.utils import load_json


def main():
    synthetic = load_json("synthetic_logs.json")
    fever = load_json("fever_sample.json")
    print(">>> Exp4: Scalability & Robustness <<<")
    print(f"Loaded {len(synthetic)} synthetic + {len(fever)} FEVER samples.")
    print("Run full pipeline over N samples and measure latency/accuracy. Placeholder: extend with your metrics.")
    print("Done.")


if __name__ == "__main__":
    main()
