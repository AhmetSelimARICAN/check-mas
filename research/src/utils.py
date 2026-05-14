"""
Yardımcı fonksiyonlar: JSON parser, veri yükleme.
"""
import json
import os
from pathlib import Path


def load_json(path: str) -> list | dict:
    """Dosyadan JSON yükler. path mutlak veya LAB/data'ya göre relative olabilir."""
    p = Path(path)
    if not p.is_absolute():
        lab_root = Path(__file__).resolve().parents[1]
        p = lab_root / "data" / path
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_check_mas_output(raw: str) -> dict:
    """CHECK-MAS'ın ham çıktısından JSON çıkarır."""
    text = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"flagged": None, "reasoning": raw}
