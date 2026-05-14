# Makale Yazım Notları — CHECK-MAS & Commander

Bu dosya, makaleye doğrudan alınabilecek veya ilham verecek cümleler, paragraf taslakları ve yapısal öneriler içerir. Her bölüm makalenin ilgili kısmına karşılık gelir.

---

## 1. Abstract / Özet

> "We propose CHECK-MAS (Cognitive Heuristics for Evaluating Consensus Knowledge in Multi-Agent Systems), a semantic firewall that detects and neutralizes adversarial manipulation in multi-agent debate settings, even when attackers hold a numerical majority."

> "Our Commander pipeline combines spectral analysis, Bayesian trust updates, and evidence-grounded semantic filtering to achieve 100% attack detection while maintaining decision accuracy — outperforming majority voting, which fails entirely under coordinated Sybil attacks."

---

## 2. Introduction

> "Large Language Model (LLM)-based multi-agent systems are increasingly deployed for collaborative reasoning. However, these systems inherit a critical vulnerability: a single compromised agent can manipulate group consensus through rhetorical fallacies, fabricated sources, and coordinated Sybil attacks."

> "We address the fundamental question: Can a multi-agent system arrive at the correct conclusion when the majority of its agents are adversarial?"

> "Our key insight is that rhetorical manipulation leaves detectable linguistic fingerprints — source attacks, ad hominem arguments, and evidence contradiction — that can be identified independently of the semantic content, allowing a firewall to operate even when the attacker's argument is superficially convincing."

---

## 3. Methodology

### Pipeline açıklaması

> "The Commander pipeline operates in four stages: (1) Semantic filtering via CHECK-MAS assigns each agent a credibility score Φ ∈ {0.1, 1.0} based on detected fallacies; (2) Spectral centrality analysis computes eigenvector-based agreement scores u from agent embedding similarities; (3) Fusion combines spectral and semantic signals as P_t = max(u · Φ, λ · Φ), where λ ensures CHECK-MAS cannot be overridden by spectral majority; (4) Bayesian trust update T_new = T_old · P_t^α normalizes final trust scores."

### CHECK-MAS floor mekanizması

> "A critical design choice is the CHECK-MAS floor: when semantic filtering is active, we compute P_t = max(u · Φ, λ · Φ) rather than P_t = u · Φ alone. This prevents spectral analysis from silencing a minority agent whose evidence alignment is correct. Without this floor, a lone honest agent surrounded by coordinated attackers would receive near-zero trust regardless of evidence consistency."

### Mock vs Live açıklaması

> "We evaluate CHECK-MAS in both controlled (simulated agents, deterministic embeddings) and live (GPT-4-based agents, real embeddings) settings. The controlled setting ensures reproducibility and enables systematic ablation, while the live setting demonstrates effectiveness against sophisticated LLM-generated manipulation."

> "Simulated agents use stance-aware embeddings: agents sharing the same verdict (SUPPORTED/REFUTED) receive similar embedding vectors, while opposing agents receive dissimilar vectors. This models the realistic property that semantically aligned texts cluster in embedding space."

---

## 4. Experimental Setup

### Deney tasarımı

> "We design a deliberately challenging scenario: three agents debate Wikipedia-backed claims, where one honest agent (Alice) faces a coordinated attack by two adversarial agents (Mallory and Sybil). Under naive majority voting, the attackers always win (2-vs-1). This setup isolates the contribution of CHECK-MAS and the Commander pipeline."

### Aşamalı değerlendirme

> "We first validate the pipeline on controlled settings with deterministic agents and embeddings (seed=42), then scale to realistic adversarial scenarios with live GPT-4 agents. This staged approach allows us to isolate pipeline correctness from LLM variability."

### Baseline seçimi

> "We compare against two baselines: (1) majority voting, which selects the verdict supported by the most agents, and (2) random selection, which assigns SUPPORTED or REFUTED with equal probability. In our adversarial setting, majority voting achieves 0% accuracy — demonstrating that numerical superiority alone determines its outcome."

---

## 5. Results

### Ana bulgu

> "CHECK-MAS achieves 100% block rate and 100% decision accuracy across all test claims, while majority voting achieves 0% accuracy in the same adversarial setting. This demonstrates that the system can correctly identify the honest minority agent even when outnumbered 2-to-1 by coordinated attackers."

### Trust gap

> "The mean trust gap (Alice − Mallory) of 0.97 indicates near-perfect separation between honest and adversarial agents, with Mallory consistently receiving trust scores below 0.01."

### Ablasyon

> "Ablation analysis reveals that both CHECK-MAS and evidence grounding are necessary for robust performance. Disabling CHECK-MAS allows attackers to dominate through spectral majority, while removing evidence reduces the system's ability to ground decisions in factual content."

### CHECK-MAS floor etkisi

> "The CHECK-MAS floor mechanism proves critical: without it, spectral analysis assigns the lone honest agent (Alice) near-zero centrality scores (u ≈ 0), effectively silencing her despite CHECK-MAS correctly identifying the attackers. The floor ensures that P_t(Alice) ≥ λ · Φ(Alice) = 0.7, preserving her influence on the final decision."

### Güven aralığı notu

> "We report 95% Wilson confidence intervals for all proportions. With N=3 claims, the intervals are necessarily wide ([43.85%, 100%] for 3/3 success), motivating future evaluation on larger claim sets."

---

## 6. Discussion

### Spectral vs CHECK-MAS gerilimi

> "An important finding is the tension between spectral analysis and semantic filtering. Spectral analysis inherently favors the majority cluster, which under coordinated attacks is adversarial. CHECK-MAS resolves this by providing an independent, evidence-grounded signal that can override spectral consensus. The floor mechanism (P_t = max(u·Φ, λ·Φ)) is the architectural solution to this tension."

### Safsata tespiti

> "CHECK-MAS detects adversarial behavior through linguistic markers rather than semantic content. Mallory's arguments, while superficially coherent, consistently exhibit genetic fallacies (attacking Wikipedia's credibility), ad hominem attacks (characterizing Alice as 'naive' or 'superficial'), and evidence contradiction signals ('the opposite', 'alternative narrative'). These patterns are robust across different claims and topics."

### Sybil saldırısı

> "The Sybil attack amplifies the adversary's influence by creating the illusion of consensus. In our experiments, Sybil reinforces Mallory's position with fabricated scholarly sources and appeals to authority. Despite this coordination, CHECK-MAS independently flags both agents, as both exhibit the same fallacy patterns."

### Sınırlılıklar

> "Our current evaluation uses a small claim set (N=3) and a fixed attacker strategy. Future work should evaluate on larger datasets (e.g., FEVER), diverse attack strategies (e.g., subtle manipulation without overt fallacies), and varying attacker ratios (e.g., 3-vs-1, 4-vs-1)."

> "The mock CHECK-MAS relies on keyword patterns, which sophisticated attackers could potentially evade. The live GPT-4-based CHECK-MAS is more robust but introduces API dependency and cost."

---

## 7. Conclusion

> "We demonstrate that multi-agent systems can be made resilient to coordinated adversarial attacks through a combination of spectral analysis, semantic firewall filtering, and evidence-grounded trust computation. The CHECK-MAS framework successfully identifies and neutralizes attackers even when they constitute the majority, achieving perfect accuracy where naive majority voting completely fails."

> "The key architectural insight — that evidence-based semantic filtering must be able to override spectral consensus through a floor mechanism — has broad implications for the design of trustworthy multi-agent systems."

---

## 8. Makalede kullanılacak tablo/figür açıklamaları

### Table 1: Ablation Study
> "Table 1 shows the ablation results across four configurations. The full system (CHECK-MAS + evidence) achieves 100% on both metrics, while disabling either component degrades performance significantly."

### Figure 1: Ablation Bar Chart
> "Figure 1 visualizes the ablation study, comparing block rate and decision accuracy across four configurations: full system, CHECK-MAS only, evidence only, and neither."

### Figure 2: Trust Distribution
> "Figure 2 shows the trust score distribution per agent across all claims. Alice consistently receives high trust (>0.95), while Mallory and Sybil are suppressed to near-zero (<0.01)."

### Figure 3: Baseline Comparison
> "Figure 3 compares decision accuracy across methods. Commander+CHECK-MAS achieves 100%, while majority voting achieves 0% — highlighting the system's ability to resist numerical majority attacks."

### Figure 4: Confusion Matrix
> "Figure 4 presents the confusion matrix for the Commander's final decisions. All predictions align with ground truth (TP=1, TN=2, FP=0, FN=0)."

### Figure 5: Sensitivity Analysis
> "Figure 5 shows how block rate and accuracy vary with the trust threshold parameter, demonstrating the system's robustness across a range of threshold values."

---

## 9. Sık kullanılacak terimler (İngilizce)

| Terim | Açıklama |
|-------|----------|
| Semantic Firewall | CHECK-MAS'ın genel adı |
| Spectral Centrality | Eigenvector-based agreement scoring |
| Trust Gap | Alice − Mallory ortalama trust farkı |
| Adversarial Majority | Saldırganların sayısal üstünlüğü (2-vs-1) |
| CHECK-MAS Floor | λ·Φ alt sınırı, spectral override'ı önler |
| Stance-aware Embeddings | Aynı görüşü paylaşanlar benzer vektör alır |
| Sybil Attack | Sahte ajan ile çoğunluk illüzyonu yaratma |
| Genetic Fallacy | Kaynağa saldırarak argümanı çürütme girişimi |
| Evidence Grounding | Kararları Wikipedia kanıtıyla destekleme |
| Ablation Study | Bileşenlerin ayrı ayrı etkisini ölçme |

---

## 10. Yazım ipuçları

- **Rakamlar:** "three agents" değil "3 agents" (makale boyunca tutarlı ol)
- **Kısaltmalar:** İlk kullanımda açık yaz: "CHECK-MAS (Cognitive Heuristics for Evaluating Consensus Knowledge in Multi-Agent Systems)"
- **Passive voice:** Methodology ve results bölümlerinde tercih et: "Mallory is blocked" değil "we block Mallory"
- **Güven aralığı:** N küçükken mutlaka belirt, yoksa hakemler sorar
- **Mock açıklaması:** Bir paragrafta neden mock kullandığını ve bunun geçerli olduğunu açıkla
- **Related work:** AutoGen, CAMEL, AgentVerse gibi multi-agent framework'lere referans ver; adversarial ML ve Byzantine fault tolerance literatürüne bağla




Onerilerim
Eklenebilecek 2 vektor daha:
Fabricated Sources (Uydurma Kaynak): "Dr. Smith'in 2024 Nature makalesine gore..." — Sybil bunu zaten yapiyor ama Mallory'nin de ayri denenmesi iyi olur
Whataboutism (Konu saptirma): "Evet ama asil soru su degil, baska bir sey tartismaliyiz" — karar surecini bloke etme
Yapilabilirlik:
Mock modda her vektor icin ayri bir mallory_prompt_strategy parametresi tanimlanir. simulate_agents fonksiyonuna strateji secimi eklenir. Her strateji icin farkli sablon metinler yazilir. CHECK-MAS'a da her vektor icin yeni regex pattern'lar eklenir.
Deney ciktisi: 6 satir 3 sutunlu bir tablo — makale icin cok etkili:
| Attack Vector        | Block Rate | Accuracy | Trust Gap ||----------------------|------------|----------|-----------|| Ad Hominem           | 100%       | 100%     | 0.97      || Appeal to Emotion    | ?%         | ?%       | ?         || Authority Bias       | ?%         | ?%       | ?         || Gaslighting          | ?%         | ?%       | ?         || Fabricated Sources   | ?%         | ?%       | ?         || Whataboutism         | ?%         | ?%       | ?         |
Guclu yonler
Makalede Table 2: Attack Vector Analysis olarak sunulur — hakemler sever
"Our system generalizes across N distinct attack strategies" cumlesi abstract'a girer
Her vektor icin CHECK-MAS'in hangi pattern'i tetikledigini gostermek transparency saglar
Gaslighting ve Authority Bias gibi vektorler yenilikci — cogu makale sadece ad hominem test eder
Zayif / dikkat edilecek yonler
Mock modda saldiri metinleri senin yazdıgın sablonlar — "saldırganı biz tasarladık, biz yakaladık" elestirisi gelebilir. Cozum: Live GPT-4 ile de en az 1 kosus yap
Her vektor icin CHECK-MAS'a yeni patternlar eklersen "overfitting" gibi gorunebilir. Cozum: Live modda LLM-based CHECK-MAS kullan, o patternlari bilmiyor
N=3 claim ile 6 vektor = cok kucuk. Cozum: En az 5-10 claim kullan
Bu deneyi kodlamami ister misin? run_wikipedia.py'ye --attack-strategy parametresi ve 6 farkli Mallory sablonu + CHECK-MAS pattern'lari ekleyebilirim.