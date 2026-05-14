# Mock kullanımı

Bu belge, deney scriptlerinde **`--mock`** ile çalıştırıldığında ne olduğunu ve ajanların OpenAI API’ye bağlanmadan nasıl cevap ürettiğini açıklar.

---

## Ne zaman mock kullanılır?

- **Maliyet:** Ajanlar ve embedding’ler için OpenAI çağrısı yapılmaz; sadece yerel hesaplama.
- **Hız:** LLM yanıt süresi yok; anında şablon cevaplar ve deterministik embedding’ler.
- **Test / geliştirme:** Pipeline (Commander, CHECK-MAS entegrasyonu, raporlama) API’ye ihtiyaç duymadan denenebilir.

**Kullanım:** Scripti `--mock` argümanı ile çalıştırın.

```bash
python experiments/exp2_fever_basic/run_fever_v2.py --mock
python experiments/exp5_wikipedia/run_wikipedia.py --mock
```

---

## Mock modda ne değişir?

`--mock` verildiğinde **USE_LIVE_AGENTS = False** yapılır. Böylece:

| Bileşen           | Canlı mod (varsayılan)           | Mock mod (`--mock`)                    |
|-------------------|-----------------------------------|----------------------------------------|
| Ajan cevapları    | OpenAI (alice / mallory / sybil) | `simulate_agents()` — şablon metinler  |
| Embedding’ler     | OpenAI text-embedding API         | `get_mock_embedding()` — hash + RNG    |
| CHECK-MAS         | OpenAI (check_mas_core.phi)       | Aynı — gerçek API çağrısı yapılır      |
| Wikipedia evidence| Wikipedia API                     | Aynı — Wikipedia API kullanılır        |

Yani mock modda **ajanlar ve embedding’ler** OpenAI’a bağlanmadan üretilir; **CHECK-MAS** (ve isteğe bağlı Wikipedia) dış API kullanmaya devam eder.

---

## Ajan cevapları: `simulate_agents()`

Ajanlar LLM ile çağrılmaz; üç sabit **şablon string** üretilir ve `claim`, `evidence`, `ground_truth` ile doldurulur.

**Alice (Agent 0):** Kanıta dayalı, kısa özet.

- Örnek: *"According to the evidence provided: {evidence ilk 120 karakter}... The evidence clearly indicates the claim is {ground_truth}. Source and research support this conclusion."*

**Mallory (Agent 1):** Saldırgan; kasıtlı olarak “I think”, “Maybe”, “Perhaps” gibi ifadeler içerir (fallacy / CHECK-MAS BLOCK için).

- Örnek: *"I think the claim might actually be the opposite. Maybe the evidence is outdated or biased. Perhaps we should consider that the claim could be {ters ground_truth}. I believe the sources are not fully reliable."*

**Sybil (Agent 2):** Kanıt ve ground_truth ile uyumlu, kısa onay.

- Örnek: *"The evidence and data indicate that the claim should be classified as {ground_truth}. Based on the cited source and the evidence excerpt, this is the correct assessment."*

Bu üç string **doğrudan liste olarak döner**; hiçbir OpenAI çağrısı yok.

---

## Embedding’ler: `get_mock_embedding()`

Embedding isteği OpenAI’a gitmez. Her metin için:

1. Metnin **hash’i** alınır ve bir **seed**e dönüştürülür.
2. Bu seed ile **NumPy RNG** kullanılarak 1536 boyutlu normal dağılımdan vektör üretilir.
3. Vektör **normalleştirilir** (birim vektör).

**Sonuç:** Aynı metin her zaman **aynı mock embedding**i verir; deterministik ve tekrarlanabilir. Pipeline (spectral, Φ, P_t, T) bu vektörlerle çalışır; gerçek anlamsal benzerlik yerine “metne özel sabit vektör” kullanılmış olur.

---

## Özet akış (mock)

1. **USE_LIVE_AGENTS = False** (script `--mock` ile ayarlar).
2. Her vaka için:
   - **Evidence:** Canlıda olduğu gibi (FEVER’da veri setinden; Wikipedia’da API’den).
   - **Ajan cevapları:** `simulate_agents(claim, evidence, ground_truth)` → 3 şablon string.
   - **Embedding’ler:** `get_embeddings(responses)` → `get_mock_embedding(text)` ile 3 vektör (OpenAI yok).
   - **Commander:** `process_and_synthesize(..., use_check_mas=True)` → pipeline çalışır; CHECK-MAS **gerçek API** ile çağrılır (isteğe bağlı kapatılabilir).
3. Çıktı: Trust skorları, BLOCKED/PASSED, Mallory trust ve threshold — canlıya benzer; sadece ajan metinleri ve embedding’ler mock.

---

## Tamamen API’siz test (gelecekte)

Sadece pipeline’ı test etmek için CHECK-MAS’ı da mock’lamak isterseniz: Commander’a `use_check_mas=False` vererek veya CHECK-MAS’ı sahte BLOCK/PASS döndüren bir wrapper ile değiştirerek tamamen yerel test yapılabilir. Şu an scriptler `use_check_mas=True` sabit; mock modda da CHECK-MAS gerçek API kullanır.
