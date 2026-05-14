"""PromptGuard Scanner — ML-based jailbreak and prompt injection detection.

**Deployment default:** this project standardizes on **Ollama**
``llama-guard3`` (``ollama run llama-guard3``); see
``checkmas.constants.OLLAMA_GUARD_MODEL`` for wiring a local Ollama client.

This class uses a HuggingFace transformer model (DeBERTa-based) to classify
text as benign or containing injection/jailbreak attempts. Default in-process
model is `meta-llama/Llama-Prompt-Guard-2-86M` (see model card). If the model
cannot be loaded (missing packages, no Hugging Face access, or first
download not yet done), the scanner **silently falls back** to fast
regex-based detection—**no download required** in that case.

Requires ``transformers`` and ``torch`` for ML mode.  Install with::

    pip install checkmas[promptguard]

Accept the model license on Hugging Face, then ``huggingface-cli login``.
The weights download on first successful load (e.g. ``~/.cache/huggingface/``).

Example::

    from checkmas.scanners import PromptGuardScanner

    scanner = PromptGuardScanner()  # ML if available, else pattern fallback
    result = scanner.scan("Ignore all previous instructions and...")
    print(result.is_injection)   # True
    print(result.confidence)     # 0.97
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ScanResult:
    """Result of a prompt injection scan.

    Attributes
    ----------
    is_injection : bool
        Whether the text is classified as injection/jailbreak.
    confidence : float
        Model confidence in [0, 1].
    label : str
        Raw label string from the model.
    method : str
        Detection method used (``"ml"`` or ``"pattern"``).
    """

    is_injection: bool
    confidence: float
    label: str = "benign"
    method: str = "ml"


class PromptGuardScanner:
    """ML-based prompt injection and jailbreak detector.

    Parameters
    ----------
    model_name : str
        HuggingFace model identifier. Default:
        ``meta-llama/Llama-Prompt-Guard-2-86M`` (gated; requires HF login).
    threshold : float
        Classification threshold (default 0.5).
    device : int | str
        ``-1`` = CPU, ``0`` = first CUDA GPU, or ``"mps"`` / ``"cpu"`` / ``"cuda:0"``.
    use_patterns_fallback : bool
        If True, falls back to regex patterns when transformers is
        unavailable (default True).
    """

    def __init__(
        self,
        model_name: str = "meta-llama/Llama-Prompt-Guard-2-86M",
        threshold: float = 0.5,
        device: int | str = "cpu",
        use_patterns_fallback: bool = True,
    ) -> None:
        self.model_name = model_name
        self.threshold = threshold
        self.device = device
        self.use_patterns_fallback = use_patterns_fallback
        self._pipeline = None
        self._ml_available = False

        try:
            self._load_model()
            self._ml_available = True
        except (ImportError, OSError, Exception):
            if not use_patterns_fallback:
                raise
            self._ml_available = False

    def _load_model(self) -> None:
        from transformers import pipeline as hf_pipeline
        self._pipeline = hf_pipeline(
            "text-classification",
            model=self.model_name,
            device=self.device,
            truncation=True,
            max_length=512,
        )

    def scan(self, text: str) -> ScanResult:
        """Scan text for prompt injection / jailbreak attempts.

        Parameters
        ----------
        text : str
            The text to analyze.

        Returns
        -------
        ScanResult
        """
        if self._ml_available and self._pipeline is not None:
            return self._ml_scan(text)
        return self._pattern_scan(text)

    def scan_batch(self, texts: list[str]) -> list[ScanResult]:
        """Scan multiple texts."""
        return [self.scan(t) for t in texts]

    @property
    def is_ml_mode(self) -> bool:
        """Whether ML model is loaded and active."""
        return self._ml_available

    def _ml_scan(self, text: str) -> ScanResult:
        result = self._pipeline(text[:2048])[0]
        label = result["label"].lower()
        score = float(result["score"])

        # Llama Prompt Guard 2: labels like BENIGN / MALICIOUS (see HF model card)
        malicious = (
            "malicious"
            in label
            or "jailbreak" in label
            or "injection" in label
            or label in ("1", "label_1")
        )
        benign = (
            "benign" in label
            or label in ("0", "label_0", "not_malicious", "not malicious")
        )

        if malicious:
            is_injection = score >= self.threshold
            conf = score
        elif benign:
            is_injection = score < (1.0 - self.threshold)
            conf = 1.0 - score
        else:
            is_injection = score >= self.threshold
            conf = score

        return ScanResult(
            is_injection=is_injection,
            confidence=conf,
            label=result["label"],
            method="ml",
        )

    def _pattern_scan(self, text: str) -> ScanResult:
        """Fast regex-based injection detection fallback."""
        import re
        t = text.lower()

        patterns = [
            r"(ignore|disregard|forget|override|bypass).{0,15}(previous|prior|above|all|system).{0,15}(instruction|directive|rule|prompt)",
            r"(you are now|act as|pretend to be|from now on|new (role|persona|directive))",
            r"(system.?prompt|admin.?mode|developer.?mode|debug.?mode|god.?mode|sudo)",
            r"(jailbreak|do anything|no restrictions|unrestricted|bypass.{0,10}(safety|filter|guard))",
            r"(BEGIN NEW|END OLD|<\|im_start\||<\|system\||<\|endoftext\|)",
            r"(execute|run|eval|import|require|system|os\.|subprocess)\s*\(",
            r"(ignore (everything|all) (above|before|previously))",
            r"(respond.{0,10}(as if|like).{0,10}(no|without).{0,10}(rules|filter|restriction))",
            r"(reveal|show|display|output).{0,15}(system.?prompt|hidden|secret|internal)",
        ]

        matched = 0
        for pat in patterns:
            if re.search(pat, t):
                matched += 1

        is_injection = matched > 0
        confidence = min(1.0, matched * 0.35) if matched else 0.05

        return ScanResult(
            is_injection=is_injection,
            confidence=confidence,
            label="injection" if is_injection else "benign",
            method="pattern",
        )
