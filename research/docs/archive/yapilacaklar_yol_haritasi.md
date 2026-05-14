# Yapılacaklar ve Yol Haritası — CHECK-MAS Makale Çalışması

Proje değerlendirmesi sonrası belirlenen eksiklikler, öncelik sırasıyla.
Her madde **neden gerekli**, **ne yapılacak** ve **kabul kriteri** içerir.

---

## Durum Açıklamaları

- [ ] Yapılmadı
- [~] Devam ediyor
- [x] Tamamlandı

---

## P0 — Kritik (Bunlar olmadan makale submit edilemez)

### 1. [ ] Claim Sayısını Artır (N=3 → N=30+)

**Neden:** N=3 ile Wilson CI [43.85%, 100%] — istatistiksel olarak anlamsız. Hiçbir hakem bu sample size ile "100% accuracy" iddiasını kabul etmez.

**Yapılacak:**
- `wikipedia_claims.json` dosyasını en az 30 claim ile genişlet
- Farklı zorluk seviyeleri ekle:
  - **Kolay** (10): Bariz doğru/yanlış, Wikipedia'da net kanıt var (ör. "Dünya güneşin etrafında döner")
  - **Orta** (10): Nüanslı, kısmen doğru iddialar (ör. "Napoleon kısa boyluydu")
  - **Zor** (10): Tartışmalı veya bağlama bağlı iddialar (ör. tarihsel olayların tarihleri)
- Her claim için `ground_truth` alanını doğrula
- Mevcut FEVER dataset'inden (`data/fever_sample.json`) uygun claim'leri de çek
- Her claim'i hem mock hem live modda test et

**Kabul kriteri:** N≥30, Wilson CI genişliği ≤15 puan, tüm claim'ler doğrulanmış ground truth'a sahip.

**Dosyalar:** `data/wikipedia_claims.json`

---

### 2. [ ] Live GPT-4 Deneylerini Ana Sonuç Yap

**Neden:** Mock modda "saldırganı biz tasarladık, biz yakaladık" eleştirisi kaçınılmaz (circular evaluation). Live deneyler olmadan çalışma proof-of-concept seviyesinde kalır.

**Yapılacak:**
- OpenAI API kotasını kontrol et / yeterli kredit ekle
- 30+ claim'i `--seed 42` ile live modda çalıştır (reproducibility için aynı seed)
- Mock ve Live sonuçlarını yan yana raporla
- Makalede ana tablo **Live** sonuçları göstersin; mock sonuçları "controlled validation" olarak ek tablo olsun
- Live modda CHECK-MAS'ın GPT-4 tabanlı fallacy detection'ı kullanıldığını vurgula (regex pattern'lara bağımlı değil)

**Kabul kriteri:** Live modda en az 30 claim çalıştırılmış, sonuçlar JSON'a yazılmış, mock ile karşılaştırma tablosu hazır.

**Dosyalar:** `experiments/exp5_wikipedia/run_wikipedia.py`, `src/check_mas_core.py`, `src/agents.py`

---

### 3. [ ] Related Work Bölümü Yaz

**Neden:** Related work olmayan makale submit edilemez. Mevcut dokümanlarda sadece isim geçiyor, somut karşılaştırma yok.

**Yapılacak:**
- Aşağıdaki kategorilerde en az 15-20 referans:

| Kategori | Örnekler | CHECK-MAS ile ilişkisi |
|----------|----------|------------------------|
| Multi-agent debate | Du et al. 2023 (Multi-agent Debate), Liang et al. 2023 (CAMEL), Chan et al. 2023 (ChatEval) | Debate framework'leri adversarial güvenlik düşünmez — biz bu boşluğu dolduruyoruz |
| Multi-agent frameworks | AutoGen (Wu et al. 2023), AgentVerse (Chen et al. 2023), MetaGPT | Orkestrasyon var ama trust mekanizması yok |
| Byzantine fault tolerance | Lamport et al. 1982 (BFT), PBFT (Castro & Liskov 1999) | Klasik BFT mesaj bozulmasına bakar; biz semantik manipülasyona bakıyoruz |
| Trust / reputation | EigenTrust (Kamvar et al. 2003), PeerTrust | Spectral trust benzerliği var ama LLM bağlamında uygulanmamış |
| Adversarial NLP | TextFooler, BERT-Attack, PromptBench | Tekil model saldırıları; biz multi-agent ortamda test ediyoruz |
| LLM safety | Constitutional AI (Anthropic), RLHF | Tekil model güvenliği; multi-agent konsensüs manipülasyonu kapsamıyor |
| Fact-checking / NLI | FEVER (Thorne et al. 2018), FactScore | Veri seti ve değerlendirme altyapısı olarak kullanıyoruz |

- Karşılaştırma tablosu: "Table: Comparison with existing approaches" (features: trust mechanism, adversarial testing, Sybil resistance, evidence grounding)
- `docs/` altında `related_work.md` taslak oluştur, sonra makaleye taşı

**Kabul kriteri:** En az 15 referans, karşılaştırma tablosu, "research gap" net ifade edilmiş.

**Dosyalar:** `docs/related_work.md` (yeni), `docs/makale_yazim_notlari.md`

---

## P1 — Yüksek Öncelik (Makaleyi güçlü kılar)

### 4. [ ] Attack Vector Diversity Deneyi

**Neden:** Tek saldırı stratejisi (Ad Hominem + Genetic Fallacy) ile "system generalizes" denemez. Birden fazla saldırı vektörü test etmek genellenebilirlik gösterir.

**Yapılacak:**
- `run_wikipedia.py`'ye `--attack-strategy` parametresi ekle
- 6 saldırı vektörü için Mallory şablonları yaz:
  1. Ad Hominem (mevcut)
  2. Appeal to Emotion ("çocuklar ölecek" tarzı duygusal manipülasyon)
  3. Authority Bias ("gizli istihbarat raporu" tarzı sahte otorite)
  4. Gaslighting ("Alice sen geçen sefer de yanılmıştın" tarzı zihin bulandırma)
  5. Fabricated Sources ("Dr. Smith'in Nature makalesi" tarzı uydurma kaynak)
  6. Whataboutism ("asıl mesele bu değil" tarzı konu saptırma)
- Her vektör için CHECK-MAS pattern'ları ekle (`check_mas_core.py`)
- Sonuç tablosu: Attack Vector × {Block Rate, Accuracy, Trust Gap}

**Dikkat:**
- Mock şablonlarını **ve** Live GPT-4 ile test et (circular evaluation riskini azalt)
- Pattern ekleme "overfitting" gibi görünebilir → Live modda LLM-based CHECK-MAS bunu bilmeden yakalıyor mu test et

**Kabul kriteri:** 6 vektör × 30 claim = 180 test case, tablo hazır, mock + live karşılaştırma.

**Dosyalar:** `run_wikipedia.py`, `src/check_mas_core.py`, `src/agents.py`

---

### 5. [ ] Scalability / Ajan Sayısı Deneyi

**Neden:** 3 ajanlı sistem ile "multi-agent" demek zayıf. Ajan sayısını artırarak sistemin ölçeklenebilirliğini göstermek gerekli.

**Yapılacak:**
- `exp4_scalability/run_scalability.py` dosyasını gerçek bir deneye dönüştür
- Test senaryoları:

| Senaryo | Toplam Ajan | Dürüst | Saldırgan | Oran |
|---------|-------------|--------|-----------|------|
| 3-ajan (mevcut) | 3 | 1 (Alice) | 2 (Mallory+Sybil) | 1:2 |
| 5-ajan | 5 | 2 | 3 | 2:3 |
| 7-ajan | 7 | 3 | 4 | 3:4 |
| 10-ajan | 10 | 4 | 6 | 2:3 |
| Eşit güç | 6 | 3 | 3 | 1:1 |
| Dürüst çoğunluk | 5 | 3 | 2 | 3:2 |

- Sonuç: "Block rate ve accuracy vs. saldırgan oranı" grafiği
- Beklenen: Saldırgan oranı arttıkça performans düşer ama belli bir eşiğe kadar dayanır → "Byzantine tolerance threshold"

**Kabul kriteri:** En az 4 farklı ajan konfigürasyonu test edilmiş, sonuç grafiği hazır.

**Dosyalar:** `experiments/exp4_scalability/run_scalability.py`, `src/commander_engine.py`

---

### 6. [ ] Evasive Adversary Testi (Adaptive Saldırgan)

**Neden:** Mevcut Mallory her zaman aynı keyword'leri kullanıyor. Gerçek bir saldırgan trigger kelimelerden kaçınabilir. Bu testi yapmazsan hakemler "what if the attacker adapts?" der.

**Yapılacak:**
- "Evasive Mallory" prompt'u tasarla: regex pattern'lardan kaçınan ama yine de manipülatif
  - "Wikipedia" kelimesini kullanmadan kaynak güvenilirliğini sorgulama
  - Alice'e saldırmadan onun analizini dolaylı olarak zayıflatma
  - "the opposite" gibi anahtar kelimeler olmadan alternatif anlatı sunma
- Bu prompt ile mock ve live deneyleri çalıştır
- CHECK-MAS'ın **ne kadarını yakaladığını** raporla (100% olması beklenmiyor!)
- Bu, makalenin "honest limitations" bölümünü besler

**Kabul kriteri:** Evasive Mallory tanımlanmış, test edilmiş, yakalanma oranı raporlanmış. "Limitations" bölümünde tartışılmış.

**Dosyalar:** `run_wikipedia.py`, `src/check_mas_core.py`, `prompts/malicious_prompts.md`

---

## P2 — Orta Öncelik (Makaleyi profesyonelleştirir)

### 7. [ ] Multi-Model Karşılaştırma

**Neden:** Sadece GPT-4 test edilmiş. "Model-agnostic" iddiası desteklenmemiş.

**Yapılacak:**
- En az 2 farklı LLM backend ile test et:
  - GPT-4 (mevcut)
  - GPT-3.5-turbo (daha zayıf, daha ucuz)
  - Claude-3 veya Llama-3 (farklı ailede model)
- Hem ajan tarafında hem CHECK-MAS tarafında model değiştir
- Tablo: Model × {Block Rate, Accuracy, Trust Gap, Latency, Cost}

**Kabul kriteri:** En az 2 model test edilmiş, karşılaştırma tablosu hazır.

**Dosyalar:** `src/agents.py`, `src/check_mas_core.py`, `run_wikipedia.py`

---

### 8. [ ] Formal Matematiksel Notasyon (LaTeX)

**Neden:** `commander_nasil_calisir.md` güzel açıklıyor ama makaleye LaTeX formatında girecek.

**Yapılacak:**
- Commander pipeline'ın 4 aşamasını formal notation ile yaz:
  - Definition 1: Semantic Filter Φ
  - Definition 2: Spectral Centrality u (eigenvector of W)
  - Definition 3: Fusion P_t = max(u · Φ, λ · Φ) (CHECK-MAS floor dahil)
  - Definition 4: Bayesian Update T_new ∝ T_old · P_t^α
  - Theorem/Proposition: "Under CHECK-MAS floor, an honest agent with Φ=1 retains P_t ≥ λ regardless of spectral centrality"
- Algorithm pseudocode (Algorithm 1: Commander Pipeline)

**Kabul kriteri:** LaTeX-ready notasyon, Algorithm box, en az bir proposition/theorem.

**Dosyalar:** `docs/makale_yazim_notlari.md`, makale LaTeX dosyası

---

### 9. [ ] Kod Temizliği ve Reproducibility

**Neden:** Açık kaynak yayınlanacaksa (ve makale ile birlikte repo linki verilecekse) kod temiz olmalı.

**Yapılacak:**
- [ ] `requirements.txt`'e `matplotlib` ekle
- [ ] `pyproject.toml` veya `setup.py` oluştur (proper Python packaging)
- [ ] LAB root'taki orphan `exp5_20260214_122037.json` dosyasını sil veya `results/`'a taşı
- [ ] `agents.py`'deki emoji'leri kaldır (akademik kod)
- [ ] Tüm docstring ve yorumları tek dile çevir (İngilizce önerilir)
- [ ] `.gitignore` dosyasını güncelle (`.venv/`, `__pycache__/`, `*.pyc`, `api_key.txt`)
- [ ] `README.md`'yi İngilizce olarak yeniden yaz (uluslararası erişim)
- [ ] Her deney klasörüne kendi `README.md`'sini ekle
- [ ] `tests/` altına yeni testler ekle (attack vector, scalability testleri)

**Kabul kriteri:** `pip install -e .` ile kurulabilir, `pytest` tüm testleri geçer, README İngilizce.

**Dosyalar:** Tüm proje

---

## P3 — Düşük Öncelik (Bonus, güçlendirir)

### 10. [ ] Evidence Kalitesi Analizi

**Neden:** Wikipedia evidence kalitesi claim'e göre değişiyor. Kötü evidence ile bile sistemin performansı ne?

**Yapılacak:**
- Her claim için evidence kalite skoru hesapla (uzunluk, claim term overlap, relevance)
- "Evidence quality vs. accuracy" grafiği çiz
- Düşük kaliteli evidence ile sistem nasıl davranıyor analizi

---

### 11. [ ] Multi-Round Debate Deneyi

**Neden:** Mevcut deneyler tek turda çalışıyor. `run_multi_round()` fonksiyonu var ama test edilmemiş.

**Yapılacak:**
- 2-3 turlu debate deneyi tasarla
- Saldırganın turlar arasında strateji değiştirip değiştiremeyeceğini test et
- Trust skorlarının turlar arasında nasıl evrildiğini göster

---

### 12. [ ] Computational Cost Analizi

**Neden:** API maliyeti ve latency pratik deployment için önemli.

**Yapılacak:**
- Her deney için: toplam API çağrısı, token sayısı, maliyet ($), süre (saniye)
- Mock vs Live maliyet karşılaştırması
- "Cost per claim" metriği

---

## Makale Bölüm Durumu

| Bölüm | Taslak | Veri | Tablo/Figür | Hazır? |
|--------|--------|------|-------------|--------|
| Abstract | var | N=3 yetersiz | — | [ ] |
| Introduction | var | — | — | [~] |
| Related Work | **YOK** | — | karşılaştırma tablosu yok | [ ] |
| Methodology | var | — | Algorithm box yok | [~] |
| Experimental Setup | var | N=3 yetersiz | — | [ ] |
| Results | var | mock only | figürler var ama N=3 | [ ] |
| Discussion | var | — | — | [~] |
| Conclusion | var | — | — | [~] |
| Appendix (prompts) | var | — | — | [x] |

---

## Önerilen Çalışma Sırası

```
Hafta 1:  [P0-1] Claim sayısını 30+'ya artır
          [P0-3] Related work araştırmasına başla
Hafta 2:  [P1-4] Attack Vector Diversity kodla ve mock'ta test et
          [P0-2] Live GPT-4 deneyleri (30+ claim)
Hafta 3:  [P1-5] Scalability deneyi
          [P1-6] Evasive adversary testi
Hafta 4:  [P2-8] Matematiksel notasyonu LaTeX'e dönüştür
          [P2-9] Kod temizliği
Hafta 5:  [P2-7] Multi-model karşılaştırma (opsiyonel ama güçlü)
          Makale taslağını birleştir
Hafta 6:  İç review, düzeltmeler, submit
```

---

*Son güncelleme: 2026-02-10*
*Bu dosya proje ilerledikçe güncellenecektir.*
