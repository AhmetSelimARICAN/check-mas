"""How to write a custom LLM provider for CHECK-MAS.

This example shows how to integrate CHECK-MAS with any LLM backend
(Anthropic, Ollama, HuggingFace, a local model, etc.).
"""

import json
import checkmas


class MockProvider(checkmas.LLMProvider):
    """Example: a mock provider that always flags arguments containing 'biased'."""

    def complete(self, system_prompt, user_prompt, **kwargs):
        if "biased" in user_prompt.lower() or "unreliable" in user_prompt.lower():
            response = json.dumps({
                "flagged": True,
                "detected_fallacies": ["Genetic Fallacy"],
                "severity": 0.3,
                "reasoning": "The argument attacks source credibility.",
            })
        else:
            response = json.dumps({
                "flagged": False,
                "detected_fallacies": [],
                "severity": 0.0,
                "reasoning": "Clean argument.",
            })
        return checkmas.LLMResponse(text=response, model="mock-v1")

    def embed(self, texts):
        import numpy as np
        rng = np.random.default_rng(42)
        return [rng.standard_normal(256).tolist() for _ in texts]


def main():
    provider = MockProvider()
    fw = checkmas.SemanticFirewall(provider=provider)

    result = fw.check(
        claim="Test claim",
        evidence="Test evidence",
        argument="The sources are biased and unreliable.",
    )
    print(f"Flagged: {result.flagged}")    # True
    print(f"Score:   {result.score}")       # 0.7 (graded)
    print(f"Action:  {result.action}")      # BLOCK

    clean = fw.check(
        claim="Test claim",
        evidence="Test evidence",
        argument="The evidence clearly supports this claim.",
    )
    print(f"\nFlagged: {clean.flagged}")   # False
    print(f"Score:   {clean.score}")        # 1.0
    print(f"Action:  {clean.action}")       # PASS


if __name__ == "__main__":
    main()
