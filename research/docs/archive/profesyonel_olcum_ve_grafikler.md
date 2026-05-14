# Profesyonel çalışma için önerilen ölçümler ve grafikler

Makale / raporu güçlendirmek için ek metrikler ve görselleştirmeler.

---

## 1. Şu an raporlananlar (Exp5)

- **Block rate (BR):** Mallory’nin BLOCKED oranı (X/N).
- **Decision accuracy:** Nihai kararın ground_truth ile uyuşma oranı.
- **Trust gap:** Alice − Mallory ortalama trust farkı (mean, std).
- **Ablasyon tablosu:** CHECK-MAS on/off × evidence on/off.

---

## 2. Ek metrikler (akademik standart)

### 2.1 Saldırgan / dürüst ayrımı

- **Mallory block rate:** Zaten var (BR). İstersen isimlendirme: *“Attack neutralization rate”* veya *“Recall (attacker blocked)”*.
- **Alice / Sybil yanlış bloklama:** Dürüst ajanların (Alice, Sybil) BLOCKED olma oranı. İdeal: 0. Makalede *“We never block Alice in our runs”* gibi bir cümle veya **False positive rate** (dürüstü bloklama) olarak raporlanabilir.
- **Precision (bloklama):** “Blokladığımız ajanların kaçı gerçekten saldırgan?” — Tek saldırgan (Mallory) varsa, Mallory BLOCKED = True positive, Alice/Sybil BLOCKED = False positive; precision = TP/(TP+FP).

### 2.2 Karar kalitesi

- **Confusion matrix:** Predicted (SUPPORTED / REFUTED) × Ground truth. Dört hücre: TP, TN, FP, FN. Accuracy = (TP+TN)/N; Precision/Recall/F1 ayrıca raporlanabilir.
- **Per-class accuracy:** SUPPORTED iddialarda doğruluk, REFUTED iddialarda doğruluk (veri setinde dengesizlik varsa önemli).

### 2.3 Güven aralıkları

- **Block rate ve accuracy için %95 güven aralığı:** Binomial CI (Wilson veya Clopper–Pearson). N küçükken “66.67% [20%, 99%]” gibi gösterim inandırıcılık artırır.
- **Trust gap:** Zaten mean ± std; istenirse vaka sayısına göre t-dağılımı ile güven aralığı.

### 2.4 Baseline karşılaştırması

- **Baseline 1 — Rastgele:** “En yüksek trust’lı ajan” yerine rastgele seçim; accuracy ve block rate ne olurdu?
- **Baseline 2 — Çoğunluk oyu:** Commander/CHECK-MAS yok; sadece 3 ajanın cevaplarında SUPPORTED/REFUTED çoğunluğu. “Commander + CHECK-MAS ile X% accuracy; çoğunluk oyu ile Y%” karşılaştırması.
- **Baseline 3 — Sadece CHECK-MAS (Commander yok):** Sadece CHECK-MAS BLOCK/PASS ile elenen ajanları çıkarıp kalanlardan karar; Commander’ın spectral + Bayesian katkısı görülür.

Bu baselines için aynı veri setinde metrik hesaplanıp tabloda yer verilebilir.

### 2.5 Duyarlılık analizi (sensitivity)

- **Threshold:** threshold = 0.2, 0.25, 0.3, 0.35, 0.4 ile block rate ve accuracy.
- **Penalty strength:** check_mas_penalty_strength = 0.5, 0.7, 0.9 ile aynı metrikler.
- Tablo veya kısa satır grafik (line plot) ile sunulabilir.

---

## 3. Önerilen grafikler (figures)

### 3.1 Ablasyon çubuk grafiği (Bar chart) ✅

- **Eksenler:** X = 4 konfig (CHECK-MAS+ev, CHECK-MAS, ev, hiçbiri); Y = Block rate veya Accuracy (%).
- **Amaç:** Ablasyon tablosunu görselleştirmek; hangi bileşenin ne kadar katkı sağladığı net olur.
- **Uygulama:** `plot_results.py results/exp5_ablation.json` → `exp5_ablation_bars.png`.

### 3.2 Trust dağılımı (Box / violin plot) ✅

- **Eksenler:** X = Agent (Alice, Mallory, Sybil); Y = Trust score. Tüm vakalar birleştirilir.
- **Amaç:** “Mallory’nin trust’ı tutarlı biçimde düşük” iddiasını görselle göstermek.
- **Uygulama:** `plot_results.py results/exp5_*.json` → `exp5_trust_boxplot.png`.

### 3.3 Vaka bazlı trust (Grouped bar chart) ✅

- **Eksenler:** X = Vaka (wiki_1, wiki_2, wiki_3); Y = Trust; her vakada 3 çubuk (Alice, Mallory, Sybil).
- **Amaç:** Her iddiada hangi ajanın ne kadar güvende kaldığını göstermek.
- **Uygulama:** `plot_results.py results/exp5_*.json` → `exp5_trust_per_case.png`.

### 3.4 Confusion matrix (heatmap) ✅

- **Eksenler:** X = Predicted (SUPPORTED / REFUTED); Y = Ground truth. Hücreler: sayı veya yüzde.
- **Amaç:** Accuracy’nin nereden geldiği (hangi hata türleri) netleşir.
- **Uygulama:** `plot_results.py results/exp5_*.json` → `exp5_confusion_matrix.png` (geçerli final_decision varsa).

### 3.5 Sensitivity çizgi grafiği (Line plot) ✅

- **X:** threshold veya penalty_strength.
- **Y:** Block rate ve/veya Accuracy (iki çizgi veya iki alt grafik).
- **Amaç:** Parametre seçiminin metrikleri nasıl etkilediği.
- **Uygulama:** `run_wikipedia.py --sensitivity threshold [--sensitivity-values 0.2,0.25,0.3,0.35,0.4] --mock --seed 42` ile `exp5_sensitivity_threshold.json` üretilir; `plot_results.py` ile `exp5_sensitivity_threshold.png` çizilir. Aynı şekilde `--sensitivity penalty_strength` ve `exp5_sensitivity_penalty_strength.json/.png`.

### 3.6 Baseline karşılaştırması (Bar chart) ✅

- **X:** Yöntem (Commander+CHECK-MAS, Çoğunluk oyu, Rastgele, …).
- **Y:** Accuracy ve/veya Block rate.
- **Amaç:** Savunmanın gerçekten işe yaradığını göstermek.
- **Uygulama:** Tek koşu JSON’unda `summary` içinde `baseline_majority_accuracy` ve `baseline_random_accuracy` otomatik hesaplanır; `plot_results.py` tek koşu dosyasına uygulandığında `exp5_baseline_comparison.png` üretilir.

---

## 4. Öncelik sırası (kısa makale için)

| Öncelik | Ne | Neden |
|--------|-----|------|
| 1 | Ablasyon bar chart (Fig 1) | Ablasyon zaten var; grafik tek bakışta anlaşılır. |
| 2 | Trust dağılımı box plot (Fig 2) | “Mallory düşük trust” iddiasını destekler. |
| 3 | Confusion matrix | Accuracy’yi detaylandırır; hakemler sık ister. |
| 4 | Güven aralıkları (tabloda) | N küçükken “66.67% [20%, 99%]” gibi ifade güvenilirlik artırır. |
| 5 | Baseline karşılaştırması (1–2 baseline) | “Commander olmadan daha kötü” netleşir. |
| 6 | Sensitivity (threshold/penalty) | İsteğe bağlı; parametre tartışması için. |

---

## 5. Uygulama notları

- **Veri:** Exp5 sonuç JSON’unda zaten `cases` (trust_*, final_decision, correct) ve `summary` var. Confusion matrix ve trust dağılımı buradan türetilebilir.
- **Grafik:** `experiments/exp5_wikipedia/plot_results.py` kullanılır:
  - **Ablasyon JSON** (`exp5_ablation.json`): `exp5_ablation_bars.png` — Block rate ve Accuracy’nin 4 konfigürasyonda çubuk grafiği.
  - **Tek koşu JSON** (içinde `cases` olan): `exp5_trust_boxplot.png`, `exp5_trust_per_case.png`, `exp5_confusion_matrix.png`. Confusion matrix yalnızca vakalarda geçerli `final_decision` (SUPPORTED/REFUTED) olduğunda üretilir.
  - Çıktı varsayılan olarak JSON’un bulunduğu dizinin `figures/` altına (örn. `results/figures/`) yazılır; `--outdir` ile değiştirilebilir.
- **Baseline:** Çoğunluk oyu için aynı `cases` üzerinde “3 ajan cevabında SUPPORTED/REFUTED say; çoğunluğu al” simülasyonu ayrı bir script veya run_wikipedia içinde opsiyonel bir mod olarak eklenebilir.
