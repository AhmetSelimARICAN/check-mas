"""Pre-download ``meta-llama/Llama-Prompt-Guard-2-86M`` into the local HF cache.

Same auth as the live test: ``HUGGINGFACE_HUB_TOKEN`` or ``checkmas/hf_token.txt``.
Accept the model license on Hugging Face first.

Usage::

  cd checkmas
  pip install huggingface_hub
  python3 examples/download_llama_prompt_guard_2.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import load_secrets  # noqa: E402
from load_secrets import ensure_hf_token  # noqa: E402


def main() -> None:
    token = ensure_hf_token()
    from huggingface_hub import snapshot_download
    model_id = "meta-llama/Llama-Prompt-Guard-2-86M"
    print(f"Downloading {model_id} to Hugging Face cache (may take several minutes)...")
    path = snapshot_download(repo_id=model_id, token=token)
    print(f"OK — snapshot at: {path}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
