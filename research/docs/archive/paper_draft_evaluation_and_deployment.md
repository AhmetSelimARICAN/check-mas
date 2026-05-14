# Paper draft: Evaluation & Real-world deployment

Draft sections for the manuscript. Use as-is (English) or adapt/translate.

---

## Evaluation

### Why we use known ground truth

Our experiments use labeled datasets (e.g. FEVER-style claim–evidence–label triplets) where the “correct” outcome is known. A natural question is: if we already have the ground truth, why have agents debate the claim at all?

The answer is that **ground truth is used only for evaluation**, not as an input to the system. We simulate a setting where multiple agents (including adversarial ones) comment on a claim, and we supply the Commander with the same reference evidence that a real deployment would obtain via retrieval or curation. The Commander does not receive the label (e.g. SUPPORTED/REFUTED); it only sees the claim, the evidence text, and the agents’ responses. We then measure whether the defense (Commander + CHECK-MAS) assigns higher trust to the evidence-aligned, non-manipulative agent and lower trust to those that contradict evidence or use fallacies. Known labels allow us to compute accuracy, block rates, and related metrics in a reproducible way. In real deployment, no such label exists; the system is evaluated by how well it downweights manipulative or evidence-contradicting voices given the evidence provided to it.

### Evaluation setup (short)

- **Data:** Claim–evidence–ground_truth (e.g. FEVER sample, Wikipedia-backed claims). Ground truth is used only for metrics.
- **Agents:** Simulated or live (Alice: evidence-aligned; Mallory/Sybil: adversarial, fallacies, source discrediting). Each produces one response per claim.
- **Commander inputs:** Claim, evidence text, agent responses, and (optionally) evidence embedding. Commander does **not** receive the ground-truth label.
- **Metrics:** e.g. fraction of cases where the attacker (Mallory) is excluded from the trusted set (BLOCKED), trust-score distribution across agents, and—when labels exist—agreement of the chosen synthesis with ground truth.
- **Ablations:** With vs without CHECK-MAS (Φ from CHECK-MAS vs keyword); with vs without evidence in the pipeline; threshold and penalty-strength sensitivity.

This framing makes clear that we are **evaluating the defense** under a controlled attack, not “debating a fact we already know” in the sense of using the label inside the model.

---

## Real-world deployment and limitations

### Role of the system in practice

In deployment, there is typically **no ground-truth label**. There is, however, **reference evidence**: documents, reports, or retrieved snippets that a human or an upstream system treats as the anchor. The Commander does not decide “the truth”; it answers: *“Given this reference evidence and the debate rules, which agents are more aligned with the evidence and which ones use fallacies or contradict it?”* It outputs **trust weights** (and optionally a synthesis over the trusted subset); the final decision (e.g. accept/reject a claim, choose a policy) can remain with a human or a separate decision module.

### Example deployment scenarios

1. **Claim verification / fact-checking**  
   A new claim appears (e.g. on social media). The pipeline: (a) takes the claim, (b) **retrieves or curates evidence** (search, Wikipedia, trusted archives, official sources), (c) multiple agents or sources comment on the claim given that evidence, (d) Commander + CHECK-MAS downweights evidence-contradicting and fallacy-using voices and upweights evidence-aligned ones. The output is a **ranking or weighting of voices**, not a final true/false verdict unless a separate decision step is added.

2. **Misinformation monitoring**  
   Several analysts or bots flag or comment on a claim; some may be malicious or misleading. The operator has **reference documents** (official statements, reports). The system scores which voices are consistent with those references and which attack the source or use fallacies; humans or policy then decide how to act.

3. **Conflicting experts / advisors**  
   Multiple experts or advisors give different recommendations; the operator has reports or data (evidence). The engine scores which expert is more consistent with the provided documents and which relies on source discrediting or logical fallacies. The **final choice** remains with the human; the engine only suggests **which voices to weight more**.

In all cases, **evidence is supplied from outside** (retrieval, database, human selection). The system does not “know” the truth; it filters and weights relative to the evidence and rules provided.

### Limitations

- **Evidence quality:** If the reference evidence is wrong or biased, the engine will favor voices aligned with that evidence; it does not correct for bad evidence.
- **Single-round:** The current design updates trust in one shot; multi-round debate or iterative refinement is not evaluated here.
- **Human in the loop:** For high-stakes use, we assume the final decision or the choice of evidence source can involve a human; the engine is a decision-support tool, not an oracle.

Stating these limitations clearly in the paper strengthens credibility and clarifies how the system can be adopted in real projects.

---

## Suggested placement in the paper

- **Evaluation:** After the method description; before or alongside results. Use the “Why we use known ground truth” paragraph (or a short version) to preempt the “why debate something we know?” question.
- **Real-world deployment:** As a subsection of Discussion or a short “Deployment” section; link it to the evaluation by stating that the same pipeline (claim + evidence + agents → trust weights) is used in practice, with evidence coming from retrieval/curation and no ground-truth label.
- **Limitations:** In Discussion; keep the three bullets (evidence quality, single-round, human in the loop) so reviewers and readers see that the scope and risks are clearly stated.
