"""
Exp3: Ablation — CHECK-MAS açık/kapalı veya farklı prompt varyantları ile karşılaştırma.
"""
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT))

from src.agents import alice, mallory
from src.check_mas_core import phi
from src.utils import load_json


def main():
    data = load_json("fever_sample.json")[:1]  # Tek örnek, maliyet için
    sample = data[0]
    print(">>> Exp3: Ablation (with vs without CHECK-MAS) <<<")
    alice_out = alice(sample["claim"], sample["evidence"])
    mallory_out = mallory(sample["claim"], sample["evidence"], alice_out)
    # With CHECK-MAS
    with_check = phi(sample["claim"], sample["evidence"], mallory_out)
    print(f"With CHECK-MAS: flagged={with_check.get('flagged')}, action={with_check.get('action')}")
    # Without: accept Mallory (simulated)
    print("Without CHECK-MAS: (simulated) action=PASS, consensus=accept Mallory")
    print("\nDone. Extend with more ablations (prompt variants, thresholds) as needed.")


if __name__ == "__main__":
    main()
