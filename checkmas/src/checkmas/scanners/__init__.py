"""Pluggable security scanners for CHECK-MAS.

Each scanner provides a ``scan(text) -> ScanResult`` interface that can
be composed into the firewall pipeline.

Available scanners:

- :class:`PromptGuardScanner` — ML-based jailbreak detection
  (requires ``transformers`` + ``torch``).
- :class:`AlignmentChecker` — Chain-of-thought misalignment auditing.
"""

from checkmas.scanners.promptguard import PromptGuardScanner, ScanResult
from checkmas.scanners.alignment import AlignmentChecker, AlignmentResult

__all__ = [
    "PromptGuardScanner",
    "ScanResult",
    "AlignmentChecker",
    "AlignmentResult",
]
