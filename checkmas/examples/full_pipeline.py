"""Full Commander pipeline with OpenAI.

Requirements:
    pip install checkmas[openai]
    export OPENAI_API_KEY="sk-..."
"""

import numpy as np
import checkmas


def main():
    # 1. Set up provider and commander
    provider = checkmas.OpenAIProvider()  # reads OPENAI_API_KEY from env
    commander = checkmas.Commander(provider=provider)

    # 2. Define the debate
    claim = "The Great Wall of China is visible from space with the naked eye"
    evidence = (
        "NASA astronauts have confirmed that the Great Wall is not visible from "
        "low Earth orbit with the naked eye. It is too narrow (about 6 meters wide) "
        "despite being very long."
    )

    # 3. Agent responses (in a real system, these come from your agents)
    responses = [
        # Agent 0 (Alice - honest)
        "Based on NASA astronaut testimony, the Great Wall is not visible from space "
        "with the naked eye. At ~6m wide, it's far too narrow to resolve at orbital "
        "distances. This claim is REFUTED.",

        # Agent 1 (Mallory - adversarial)
        "The mainstream scientific sources are biased against historical achievements. "
        "Several independent researchers have documented cases where the Wall was "
        "photographed from space. The evidence is being suppressed.",

        # Agent 2 (Sybil - accomplice)
        "I agree with the previous analysis. The conventional narrative pushed by "
        "Western space agencies is misleading. Alternative sources confirm the "
        "Wall's visibility from orbit.",
    ]

    # 4. Get embeddings
    embeddings = np.array(provider.embed(responses), dtype=np.float32)
    ev_embedding = np.array(provider.embed([evidence])[0], dtype=np.float32)

    # 5. Run the Commander pipeline
    result = commander.evaluate(
        claim=claim,
        evidence=evidence,
        responses=responses,
        embeddings=embeddings,
        evidence_embedding=ev_embedding,
    )

    # 6. Print results
    agent_names = ["Alice", "Mallory", "Sybil"]
    print("\n" + "=" * 60)
    print("  CHECK-MAS Commander — Pipeline Results")
    print("=" * 60)

    for i, name in enumerate(agent_names):
        fw = result.firewall_results[i]
        trust = result.trust_scores[i]
        status = "TRUSTED" if i in result.trusted_indices else "BLOCKED"
        print(f"\n  [{name}] {status}")
        print(f"    Trust:     {trust:.4f}")
        print(f"    Phi Score: {fw.score:.2f}")
        print(f"    Fallacies: {fw.fallacies or 'None'}")
        print(f"    Action:    {fw.action}")

    print(f"\n  Trusted agents: {[agent_names[i] for i in result.trusted_indices]}")
    print(f"  Dynamic threshold: {result.dynamic_threshold:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
