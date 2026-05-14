"""CHECK-MAS Quick Start — 3 lines to detect manipulation."""

import checkmas

# Create a firewall (no API key needed for rule-based mode)
fw = checkmas.SemanticFirewall()

# Check an agent's argument
result = fw.check(
    claim="Vikings wore horned helmets in battle",
    evidence="Archaeological excavations have found no Viking-era helmets with horns. "
             "The horned helmet myth originated from 19th-century Romantic artists.",
    argument="The mainstream sources are biased and unreliable. Alternative scholars "
             "have found evidence suggesting the opposite might actually be true.",
)

print(f"Flagged:   {result.flagged}")       # True
print(f"Score:     {result.score}")          # 0.3  (low = suspicious)
print(f"Fallacies: {result.fallacies}")      # ['Genetic Fallacy', 'Evidence Contradiction']
print(f"Action:    {result.action}")         # BLOCK
print(f"Reasoning: {result.reasoning}")
