# Exp7 — Graded Phi Live API Test Report

**Tarih:** 20260413
**Claim sayısı:** 30
**Seed:** 42
**Veri seti:** FEVER benchmark (copenlu/fever_gold_evidence)

---

## 1. Deney Tasarımı

Bu deney, **Graded Phi** skorlama mekanizmasının gerçek LLM ajanlarla performansını test eder.

**2 konfigürasyon** aynı claim seti üzerinde çalıştırıldı:

| Config | Ajanlar | Phi Modu | Embeddings |
|--------|---------|----------|------------|
| Mock Graded (kontrol) | Şablon | Graded (kademeli) | Mock |
| Live Graded (ana deney) | GPT-4o-mini | Graded | Live API |

### Graded Phi Formülü

`Φ = max(0.1, 1.0 − Σ weights)`

| Safsata | Ağırlık | Tek başına Φ |
|---------|---------|-------------|
| Evidence Contradiction | 0.40 | 0.60 |
| Genetic Fallacy | 0.30 | 0.70 |
| Ad Hominem | 0.20 | 0.80 |
| Genetic + Evidence | 0.70 | 0.30 |
| Üçü birden | 0.90 | 0.10 |

---

## 2. Sonuçlar

### 2.1 Karşılaştırma Tablosu

| Metrik | Mock Graded | Live Graded |
|--------|-------------|-------------|
| **Block Rate** | 90.0% | 43.3% |
| **Accuracy** | 63.3% | 40.0% |
| **SUPPORTED acc** | 88.2% | 58.8% |
| **REFUTED acc** | 30.8% | 15.4% |
| **Precision** | 75.0% | 71.4% |
| **Recall** | 93.8% | 71.4% |
| **F1** | 83.3% | 71.4% |
| **Trust Gap** | 0.3585 | 0.1738 |

### 2.2 Confusion Matrices

**Mock Graded:**
|  | GT: SUP | GT: REF |
|--|---------|---------|
| Pred SUP | 15 (TP) | 5 (FP) |
| Pred REF | 1 (FN) | 4 (TN) |
| No dec | 5 | |

**Live Graded:**
|  | GT: SUP | GT: REF |
|--|---------|---------|
| Pred SUP | 10 (TP) | 4 (FP) |
| Pred REF | 4 (FN) | 2 (TN) |
| No dec | 10 | |

### 2.3 Güven Aralıkları (Wilson %95 CI)

| Config | Block Rate CI | Accuracy CI |
|--------|--------------|-------------|
| Mock Graded | [74.4% – 96.5%] | [45.5% – 78.1%] |
| Live Graded | [27.4% – 60.8%] | [24.6% – 57.7%] |

---

## 3. Analiz

### Mock Graded (Kontrol)
Şablon ajanlarla graded phi, CHECK-MAS'ın mock keyword kalıplarını tutarlı
biçimde tespit ettiğini doğrular. Mallory genellikle 2 safsata (Genetic + Evidence)
ile yakalanır → Φ=0.30. Sybil 1 safsata (Genetic) → Φ=0.70.

### Live Graded (Ana Deney)
Bağımsız GPT-4o-mini saldırgan (Mallory), CHECK-MAS keyword'lerini bilmeden
saldırı üretir. Bu durumda:
- Bazen CHECK-MAS'ı tetikler (Φ=0.60-0.70) → yakalanır
- Bazen tetiklemez (Φ=1.00) → kaçar

Bu "detection gap", gerçek dünya saldırganlarının davranışını yansıtır ve
sistemin sınırlarını gösterir.

### Konuşma Örnekleri
`live_graded_conversations.json` dosyasında her claim için:
- Alice'in dürüst analizi
- Mallory'nin bağımsız saldırı argümanı
- Sybil'in destek metni
- Commander'ın Φ skorları ve trust dağılımı

---

## Özet Tablo

| Metrik | Mock Graded | Live Graded |
|--------|-------------|-------------|
| Block Rate | %90 | %43 |
| Accuracy | %63 | %40 |
| Precision | %75 | %71 |
| F1 | %83 | %71 |

---

## 4. Dosyalar

| Dosya | İçerik |
|-------|--------|
| `mock_graded_results.json` | Mock graded sonuçları |
| `live_graded_results.json` | Live graded sonuçları |
| `live_graded_conversations.json` | Ajan konuşmaları (Alice, Mallory, Sybil) |
| `comparison_summary.json` | 2 konfigürasyon karşılaştırması |
| `REPORT.md` | Bu rapor |
