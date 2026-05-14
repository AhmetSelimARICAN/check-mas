"""Load API / Hugging Face tokens from env or project token files.

Looks for (in order):
  - ``HUGGINGFACE_HUB_TOKEN`` / ``HF_TOKEN`` (env)
  - ``hf_token.txt`` next to this file's parent, or repo root, or ``~/hf_token.txt``
  - ``api_key.txt`` for OpenAI (``sk-...``) in same locations as Exp8

Does not log token values.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

# examples/load_secrets.py -> checkmas/
_CHECKMAS = Path(__file__).resolve().parent.parent
_REPO = _CHECKMAS.parent
_SEARCH_BASES = [_REPO, _CHECKMAS]


def _parse_hf_token_file(path: Path) -> str | None:
    """First token-like line: ``hf_...`` (Hugging Face read tokens; tolerate BOM, quotes, export lines)."""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    for line in raw.splitlines():
        line = line.lstrip("\ufeff").strip()
        if not line or line.startswith("#"):
            continue
        if "HUGGINGFACE" in line or "HF_TOKEN" in line:
            m = re.search(r"hf_[A-Za-z0-9_\-]+", line)
            if m:
                return m.group(0)
        m = re.search(r"hf_[A-Za-z0-9_\-]+", line)
        if m:
            return m.group(0)
    m = re.search(r"hf_[A-Za-z0-9_\-]+", raw)
    return m.group(0) if m else None


def _read_hf_token() -> str | None:
    # Prefer repo / checkmas ``hf_token.txt`` over env and ``hf auth`` cache so a refreshed file wins.
    for base in _SEARCH_BASES:
        f = base / "hf_token.txt"
        if f.is_file():
            t = _parse_hf_token_file(f)
            if t:
                return t
    for key in ("HUGGINGFACE_HUB_TOKEN", "HF_TOKEN"):
        v = os.environ.get(key, "").strip()
        if v:
            return v
    try:
        from huggingface_hub import get_token

        t2 = get_token()
        if t2:
            return t2.strip()
    except Exception:
        pass
    return None


def _read_openai_key() -> str | None:
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"].strip()
    for base in _SEARCH_BASES:
        f = base / "api_key.txt"
        if f.is_file():
            raw = f.read_text(encoding="utf-8", errors="ignore").strip()
            m = re.search(r"sk-[a-zA-Z0-9\-_]+", raw)
            if m:
                return m.group(0)
    return None


def ensure_hf_token() -> str:
    """Set ``HUGGINGFACE_HUB_TOKEN`` and return the token, or raise."""
    t = _read_hf_token()
    if not t:
        raise RuntimeError(
            "Hugging Face token missing. Gated model requires login.\n"
            "1) Accept the license: https://huggingface.co/meta-llama/Llama-Prompt-Guard-2-86M\n"
            "2) Create a token: https://huggingface.co/settings/tokens\n"
            "3) Run: hf auth login   (or set HUGGINGFACE_HUB_TOKEN / hf_token.txt)"
        )
    os.environ["HUGGINGFACE_HUB_TOKEN"] = t
    return t


def ensure_openai_key() -> str:
    t = _read_openai_key()
    if not t:
        raise RuntimeError(
            "OpenAI API key missing. Set OPENAI_API_KEY or add api_key.txt (sk-...)."
        )
    os.environ["OPENAI_API_KEY"] = t
    return t


def login_huggingface() -> None:
    """Put Hugging Face token in env (from file, env var, or ``hf auth login`` cache)."""
    ensure_hf_token()
