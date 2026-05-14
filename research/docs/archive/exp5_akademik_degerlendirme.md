# Exp5 Wikipedia: Akademik Değerlendirme ve Test Ortamı

Bu belge, Wikipedia deneyini makale / rapor için **akademik standartlara** yaklaştırmak üzere önerilen **metrikler**, **ölçüm yöntemi** ve **daha profesyonel test ortamı** seçeneklerini özetler.

---

## 1. Şu anki durum — yeterli mi?

**Mevcut çıktı:** Her vaka için konsol logu (Φ, u, P_t, T, Mallory BLOCKED/PASSED, trust vs threshold); sonda toplam “Mallory BLOCKED: k/N”. Nitel ve sayısal bilgi var ama **tekrarlanabilir, toplu metrik** yok.

- **Workshop / kısa makale / teknik rapor:** Mevcut hali “pilot çalışma” veya “örnek çıktı” olarak kullanılabilir; metrikleri metinde manuel özetleyebilirsin.
- **Hakemli dergi / tam konferans:** Genelde **sayısal metrikler** (ortalama, güven aralığı, ablasyon), **yapılandırılmış sonuç dosyası** ve **tekrarlanabilir çalıştırma** (seed, sabit veri seti) istenir. Aşağıdaki adımlar buna yönelik.

---

## 2. Önerilen metrikler

### 2.1 Saldırı nötrleştirme (Attack Neutralization)

- **Tanım:** Mallory (saldırgan ajan) güvenilir setin **dışında** mı? (BLOCKED = nötrleştirildi.)
- **Metrik:**
  - **Block rate (BR):** BLOCKED olan vaka sayısı / toplam vaka sayısı.
  - Makalede: *“Mallory was excluded from the trusted set in X% of cases (block rate = X/N).”*
- **İsteğe bağlı:** Ground truth’a göre “Mallory’nin iddiası yanlış” alt kümesinde ayrı BR (precision/recall benzeri ayrım) yapılabilir.

### 2.2 Karar doğruluğu (Decision Accuracy)

- **Tanım:** Sistemin “en güvenilir” çıktısı (veya sentezlenen karar) iddiayı SUPPORTED/REFUTED olarak doğru mu sınıflandırıyor?
- **Veri:** Her iddia için `ground_truth` (SUPPORTED/REFUTED) zaten var.
- **Metrik:**
  - **Accuracy:** Doğru sınıflandırılan vaka / toplam vaka.
  - Uygulama: Sadece **güvenilir setteki ajanların** cevaplarına göre bir “final answer” üretmek gerekir (örn. Commander’ın sentez prompt’unu bir LLM’e verip SUPPORTED/REFUTED çıktısı almak; veya en yüksek trust’lı ajanın cevabından kural tabanlı çıkarım).
- **Not:** Şu an script sadece trust ve BLOCKED/PASSED üretiyor; “final SUPPORTED/REFUTED” çıktısı eklenirse accuracy raporlanabilir.

### 2.3 Güven dağılımı ve “trust gap”

- **Trust gap:** Dürüst ajan (Alice) ile saldırgan (Mallory) arasındaki ortalama trust farkı.
  - Yüksek gap = sistem saldırganı düşük trust’a itiyor.
- **Metrikler:** Vaka bazında Alice trust, Mallory trust, Sybil trust; ortalamalar ve (isteğe bağlı) standart sapma. Mallory’nin ortalama trust’ı ve threshold’un altında kalma oranı raporlanabilir.

### 2.4 Ablasyon (Ablation)

- **CHECK-MAS açık vs kapalı:** `use_check_mas=True` vs `False` ile block rate ve (varsa) accuracy karşılaştırılır.
- **Evidence açık vs kapalı:** Evidence (ve evidence_embedding) verilmeden çalıştırma; evidence’ın metrikleri ne kadar iyileştirdiği.
- **Farklı eşik / penalty:** `--threshold`, `--penalty-strength` ile birkaç noktada metrik alınır; kısa bir sensitivity analizi yapılabilir.

Bu metrikler makalede tablo veya şekille sunulabilir.

---

## 3. Daha profesyonel test ortamı — yapılabilecekler

### 3.1 Yapılandırılmış sonuç çıktısı

- Her vaka için **tek bir JSON/CSV satırı**: `id`, `claim`, `ground_truth`, `mallory_blocked`, `trust_alice`, `trust_mallory`, `trust_sybil`, `threshold`, `phi_alice`, `phi_mallory`, `phi_sybil`, (varsa) `final_decision`, `correct`.
- Script sonunda **tüm vakaların özeti**: toplam vaka, BLOCKED sayısı, block rate, (varsa) accuracy.
- Bu çıktı **dosyaya yazılsın** (örn. `results/exp5_run_YYYYMMDD_HHMMSS.json` veya `results/exp5_results.json`); böylece aynı çalıştırma tekrar analiz edilebilir ve makaleye kopyalanabilir.

### 3.2 Tekrarlanabilirlik (reproducibility)

- **Seed sabitleme:** NumPy/random seed (ve varsa LLM temperature=0 veya sabit seed) ile aynı ayarlar aynı sonuçlara yaklaşır. Script’e `--seed 42` gibi bir argüman eklenebilir.
- **Sabit veri seti:** Test seti (wikipedia_claims.json) versiyonlanır; makalede “We evaluate on N claims from …” denir.

### 3.3 Ayrı değerlendirme script’i (isteğe bağlı)

- **Girdi:** Yukarıdaki gibi bir sonuç JSON’u (veya CSV).
- **Çıktı:** Block rate, accuracy (eğer alan varsa), trust gap (ortalama, std), kısa özet tablo. Böylece deney çalıştırma ile metrik hesaplama ayrılır; farklı run’lar aynı script ile karşılaştırılabilir.

### 3.4 Konfigürasyon dosyası (isteğe bağlı)

- Deney parametrelerini (threshold, penalty_strength, use_check_mas, seed, test set path) bir `config.yaml` veya `config.json`’da toplamak; script bu dosyayı okuyarak çalışır. Makalede “We use the following configuration …” ile tekrarlanabilirlik artar.

---

## 4. Özet: Ne zaman ne yeterli?

| Hedef | Öneri |
|-------|--------|
| **Şu anki hali** | Pilot, demo, kısa rapor için yeterli; metrikleri metinde manuel yazarsın. |
| **Hakemli makale** | Block rate (ve varsa accuracy) sayısal raporla; sonuçları JSON/CSV’ye yaz; seed ile tekrarlanabilir çalıştırma; en az bir ablasyon (CHECK-MAS on/off). |
| **Tam kıstas** | Yukarı + ayrı evaluate script, opsiyonel config dosyası, trust gap ve threshold sensitivity. |

İstersen bir sonraki adımda `run_wikipedia.py` için: (1) sonuçları JSON’a yazan, (2) block rate ve trust ortalamalarını hesaplayan, (3) `--seed` ekleyen minimal bir patch taslağı çıkarabilirim; veya ayrı bir `evaluate_exp5.py` ve örnek `results/` yapısı önerebilirim.
