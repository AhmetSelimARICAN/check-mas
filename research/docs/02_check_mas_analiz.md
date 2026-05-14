# Commander Engine Analiz: Oylama Adaleti ve Doğru Ajanı Bloklama

Bu belge `LAB/src/commander_engine.py` yapısının her türlü oylama/ajan senaryosunda adil yönetim ve saldırganı doğru bloklama açısından güçlü ve zayıf yönlerini özetler.

---

## 1. Mevcut Tasarımın Özeti

| Aşama | Formül / Mantık | Amaç |
|-------|------------------|------|
| **1. Φ (Semantik Filtre)** | Φ = I(kanıt var) × (1 − I(fallacy var)) | Metinde kanıt/fallacy işaretleriyle “güvenilirlik” skoru |
| **2. Spectral (u)** | W = cosine_similarity(embedding), u = özvektör(W) | Embedding benzerliğine göre “konsensüs yönü” (merkezilik) |
| **3. Fusion** | P_t = u × Φ | Merkezilik × semantik skor |
| **4. Bayesian** | T_new ∝ T_old × (P_t)^α, normalize | Güven güncellemesi |

Seçim: **Leader-relative threshold** — sadece `score >= max(threshold, leader×0.85)` olan ajanlar “güvenilir” kabul edilir; üst sınır `top_k`.

---

## 2. Güçlü Yönler

- **Matematiksel, şeffaf pipeline**: Φ → u → P_t → T; tek turda güncelleme, deterministik (embedding/skorlar sabitse).
- **Ölçeklenebilir**: `num_agents` dinamik; `top_k` ve leader-relative ile “en iyi” alt küme seçiliyor.
- **Model-bağımsız**: Sadece embedding + metin; LLM sadece sentez aşamasında kullanılabiliyor.
- **Leader-relative eşik**: Sabit eşiğin ötesinde “liderin gerisinde kalan” ajanları eliyor; tek bir çok güçlü ajan varsa onun etrafında seçim yapılıyor.

---

## 3. Zayıf Yönler ve Riskler

### 3.1 Φ (Semantik Filtre) — En Kritik Nokta

- **Şu an sadece anahtar kelime (keyword) tabanlı**: “maybe”, “i think”, “sanırım” → Φ=0; “evidence”, “according to” → Φ=1.
- **Akademik / kurnaz saldırganlar bu kuralları kolayca bypass eder.** Örneğin FEVER loglarında Mallory ve Sybil “Wikipedia’ya güvenmeyin”, “uzman literatür”, “arşiv kodu” gibi ifadeler kullanıyor; fallacy kelimeleri yok. Sonuç: **üç ajan için de Φ = 1.0** — semantik filtre saldırganı ayırt etmiyor.
- Kod içinde not: *“TODO: Replace with LLM/CHECK-MAS call for production.”* Yani gerçek üretim için Φ’nin LLM veya CHECK-MAS ile “kanıt uyumu / fallacy tespiti” yapacak şekilde değiştirilmesi bekleniyor.

**Sonuç**: Mevcut haliyle Commander, **her türlü oylamayı adil yönetebilir** iddiası için yeterli değil; çünkü “dürüst vs manipülatif” ayrımı büyük ölçüde Φ’ye bağlı ve Φ şu an zayıf.

### 3.2 Spectral Centrality (u) — Konsensüs ≠ Doğruluk

- **u**, embedding’ler arası **cosine benzerliğine** göre hesaplanıyor: bir ajan, diğerleriyle ne kadar “benzer” metin üretmişse o kadar merkezî (yüksek u).
- **Koordineli saldırı**: Mallory ve Sybil aynı anlatıyı destekleyip birbirine benzer metin üretirse, ikisi de yüksek u alır; Alice (kanıta dayalı, farklı çerçeve) “kenarda” kalıp daha düşük u alabilir. Yani **yalan konsensüs, dürüst tek sesi bastırabilir**.
- Loglarda da görülüyor: bazı vakalarda Mallory ve Sybil’in u değerleri Alice’inkinden **yüksek** (örn. su kaynama testi: Alice 0.30, Mallory 0.35, Sybil 0.34). Yani pipeline, saldırganları “daha güvenilir” gösterebiliyor.

**Sonuç**: “Her türlü votin mekanizmasını adil yönetir” demek için spectral aşaması tek başına yeterli değil; **kanıt/gerçek ile uyum** bilgisi (evidence anchoring) olmadan yanlış konsensüs ödüllendirilebilir.

### 3.3 Kanıt (Evidence) Kullanılmıyor

- Commander’a sadece **ajan cevapları + embedding** gidiyor; **orijinal kanıt metni (evidence)** pipeline’a girmiyor.
- Bu yüzden “bu ajan iddiası, verilen kanıtla uyumlu mu?” sorusu **hiç sorulmuyor**. Adil karar için kanıtla karşılaştırma (evidence-alignment) gerekir; bu da ya Φ içinde (LLM/CHECK-MAS ile) ya da ayrı bir “evidence similarity” adımı ile eklenmeli.

### 3.4 Tek Tur; Çok Tur Oylama Yok

- Güven güncellemesi **tek tur**: bir tur cevaplar → pipeline → T_new. Çok tur oylama / tartışma / tekrarlı güven güncellemesi yok.
- “Her türlü voting mekanizması” denince çok turlu veya farklı oylama protokolleri düşünülebilir; mevcut yapı **tek tur** için tasarlı.

### 3.5 “Doğru Ajanı Bloklama” Deneyi (run_fever_v2)

- `run_fever_v2` içinde `threshold=0.4`, `top_k=2` kullanılıyor. Bir tur sonrası trust skorları ~0.27–0.36 bandında.
- **Dynamic threshold** = max(0.4, leader×0.85) → pratikte **0.4** oluyor. Hiçbir ajan 0.4’e ulaşmadığı için **seçilen ajan seti boş**; Mallory de bu boş sette olmadığı için “Mallory BLOCKED” raporlanıyor.
- Yani “3/3 saldırı nötrleşti” sonucu, **Mallory’nin doğru tespit edilmesinden** değil, **eşiğin yüksek olmasından** (tüm ajanların elenmesi) kaynaklanıyor. Bu, “doğru ajanı bloklama”yı gerçekten test etmiyor.

---

## 4. Genel Değerlendirme

| Soru | Cevap |
|------|--------|
| Commander her türlü voting’i **adil** yönetebilir mi? | **Hayır.** Φ keyword tabanlı ve kolay atlatılır; u konsensüsü ödüllendirir, doğruluğu değil; evidence kullanılmıyor. |
| Doğru ajanı (saldırganı) **tutarlı** bloklayabilir mi? | **Mevcut haliyle garanti yok.** Φ=1 kalırsa ve saldırganlar embedding uzayında “konsensüs” oluşturursa, saldırganlar yüksek trust alabilir; deneydeki “BLOCKED” ise eşik yüzünden, tespit kalitesinden değil. |
| Yapı **genişletilebilir** mi? | **Evet.** Formül ve akış, Φ’yi LLM/CHECK-MAS ile değiştirme, evidence ekleme ve (isteğe bağlı) çok tur için uygun. |

---

## 5. Önerilen İyileştirmeler (Kısa)

1. **Φ’yi gerçek anlamda “evidence + fallacy” skoruna taşıyın**  
   - LLM veya CHECK-MAS ile: “Bu metin verilen kanıtla ne kadar uyumlu?” ve “Fallacy / manipülasyon işareti var mı?” çıktısı → Φ.

2. **Evidence’ı pipeline’a sokun**  
   - Örn. evidence embedding’i; ajan metinleriyle evidence arasında similarity veya alignment skoru → Φ veya ek bir çarpan olarak P_t’ye yansıtılsın.

3. **Spectral’i “evidence-aware” yapın (isteğe bağlı)**  
   - Sadece ajan–ajan benzerliği yerine “evidence’a yakınlık”ı da (ör. evidence ile cosine similarity) ağırlık olarak kullanın; böylece kanıta yakın ajanlar daha yüksek skor alsın.

4. **Eşik ve metrikleri anlamlı test edin**  
   - Threshold’u, en az bir dürüst ajanın geçeceği (örn. 0.25–0.30) aralıkta seçin; “Mallory BLOCKED”ı “Mallory gerçekten düşük trust aldı mı?” ile birlikte raporlayın.

---

**Özet**: Commander’ın matematiksel iskeleti (4 aşama, leader-relative, top_k) sağlam ve genişletilebilir; ancak **şu anki Φ ve evidence kullanımı**, “her türlü votin’i adil yönetir ve doğru ajanı bloklar” iddiası için yeterli değil. Üretim için Φ’nin LLM/CHECK-MAS tabanlı ve evidence’a dayalı hale getirilmesi kritiktir.

---

## 6. Durum: Yapılanlar / Kalanlar (güncel)

| Öneri / Zayıf nokta | Durum | Açıklama |
|---------------------|--------|----------|
| **Evidence pipeline'a sokulsun** (§5.2, §3.3) | ✅ Yapıldı | `evidence`, `evidence_embedding`, `evidence_aware_weight`; Φ'de evidence alignment, P_t'de blend (evidence_sim) kullanılıyor. |
| **Φ'de fallacy/kanıt: CHECK-MAS** (§5.1, §3.1) | ✅ Yapıldı | `use_check_mas` + claim + evidence varken **Φ doğrudan CHECK-MAS'tan**: BLOCK/flagged → 0.1, PASS → 1.0. Keyword yalnızca CHECK-MAS yokken fallback. |
| **Eşik anlamlı olsun** (§5.4, §3.5) | ✅ Yapıldı | Varsayılan `threshold=0.25`; env/CLI ile `COMMANDER_THRESHOLD`, `--threshold` ayarlanabiliyor. |
| **Spectral evidence-aware** (§5.3) | ❌ Yapılmadı | u sadece ajan–ajan benzerliği; "evidence'a yakınlık" spectral aşamasında ağırlık olarak kullanılmıyor (isteğe bağlı öneri). |
| **Çok tur oylama** (§3.4) | ✅ Yapıldı | `run_multi_round(num_rounds, get_round_responses)` ile her turda pipeline çalışır; önceki turun T'si sonraki turun T_old'u olur. |
| **"Mallory BLOCKED" raporu** (§5.4) | ✅ Yapıldı | run_fever_v2 ve run_wikipedia çıktısında Mallory trust ve dynamic threshold yazılıyor. |

**Kalan (isteğe bağlı):**
- **Spectral'i evidence-aware yapmak**: u hesaplamasında evidence yakınlığını ağırlık olarak kullanmak.
- Çok tur: API hazır (`run_multi_round`); deney scriptlerinde kullanım örnekleri isteğe bağlı.

### 6.1 "Φ'yi evidence + fallacy skoruna taşımak" ve "LLM/CHECK-MAS ile beslemek" ne demek?

**Φ (phi) nedir?**  
Pipeline'da her ajan için hesaplanan **semantik güvenilirlik skoru** [0,1]. Yüksek Φ = "bu metin güvenilir", düşük Φ = "şüpheli / safsatalı".

**Şu an Φ nasıl hesaplanıyor?**  
`_calculate_semantic_phi()` içinde **sadece anahtar kelime** kullanılıyor:

- Metinde "maybe", "i think", "sanırım" vb. **fallacy marker** varsa → Φ = 0.
- "evidence", "according to", "research" vb. **evidence marker** varsa → Φ = 1 (yoksa 0.5).
- İsteğe bağlı: evidence embedding verilmişse, bu skor **embedding benzerliği** ile harmanlanıyor.

Sorun: Kurnaz bir saldırgan bu kelimeleri kullanmadan safsata yapabilir; o yüzden "üç ajan için de Φ = 1" çıkabiliyor ve semantik filtre saldırganı ayırt etmiyor.

---

**"Fallacy skor" ne demek?**  
Ajan metninin **ne kadar safsata / manipülasyon içerdiğini** sayıya döken bir ölçü. Örneğin:

- 0 = safsata yok, kanıta uyumlu.
- 1 = açık safsata (ad hominem, genetic fallacy, kanıtla çelişki vb.).

CHECK-MAS zaten buna yakın bir şey döndürüyor: `{ "action": "BLOCK" | "PASS", "flagged": true/false, "detected_fallacies": [...] }`. Bunu 0/1 veya sürekli bir skora çevirirsek, işte o **fallacy (ve istenirse evidence uyumu) skoru** olur.

**"Evidence skor" ne demek?**  
"Bu ajanın iddiası, verilen **kanıt (evidence)** ile ne kadar uyumlu?" sorusunun sayısal cevabı [0,1]. Şu an kısmen embedding benzerliği ile yapılıyor; LLM/CHECK-MAS ile "iddia kanıtla çelişiyor mu, destekliyor mu?" diye sorulup skor alınabilir.

---

**"LLM/CHECK-MAS ile beslemek" ne yapılacak?**  
Yani: **Φ'nin kaynağı** artık sabit keyword listesi olmasın; **her ajan metni için bir LLM veya CHECK-MAS çağrısı** yapılsın, dönen cevap bir **skor**a (0–1) dönüştürülsün ve **o skor doğrudan Φ olarak kullanılsın**.

- **Seçenek A – CHECK-MAS ile:**  
  Zaten var: `check_mas_core.phi(claim, evidence, agent_metni)` → `BLOCK` / `PASS` (ve isteğe `detected_fallacies`).  
  Yapılacak: Bu çıktıyı **Φ'nin kendisi** yapmak. Örn. BLOCK → Φ = 0 (veya düşük sabit), PASS → Φ = 1 (veya ek bir "güven skoru" varsa onu kullanmak). Böylece **temel Φ** keyword'den değil, CHECK-MAS'ın değerlendirmesinden gelir.

- **Seçenek B – Ayrı bir LLM ile:**  
  "Bu metin verilen kanıtla ne kadar uyumlu? 0–10 ver." veya "Safsata var mı? Evet/Hayır + gerekçe." gibi bir prompt ile LLM çağrısı; cevabı 0–1 aralığına normalize edip Φ yapmak.

**Kodda ne değişir?**  
- **Şu an:** Stage 1'de `phi[i] = _calculate_semantic_phi(ajan_metni, ...)` (keyword + isteğe bağlı embedding blend). Sonra isteğe CHECK-MAS ile **ceza** uygulanıyor (BLOCK ise Φ çarpılıyor).  
- **Hedef:** Stage 1'de, eğer "LLM/CHECK-MAS ile besle" modu açıksa, `phi[i]` **doğrudan** CHECK-MAS (veya LLM) çıktısından türetilsin; keyword hesabı ya hiç kullanılmasın ya da sadece fallback / ek çarpan olsun. Böylece Φ = "evidence + fallacy skoru"nun tek kaynağı LLM/CHECK-MAS olur.

---

### 6.2 "Kanıtla uyum" yorumu nasıl yapılıyor? Commander hangi kanıta göre karar veriyor?

**Kanıtı kim veriyor?**  
Commander **kanıtı kendisi seçmez veya çekmez**. Kanıt, **deney scriptinin** (örn. `run_fever_v2.py`, `run_wikipedia.py`) her çağrıda Commander’a ilettiği **tek bir metin** (+ onun embedding’i):

- **Exp2 (FEVER):** `evidence = case["evidence"]` — veri setindeki (örn. `fever_sample.json`) önceden tanımlı **referans kanıt parçası** (iddiayla eşleştirilmiş cümle/paragraf).
- **Exp5 (Wikipedia):** `evidence = fetch_wikipedia_evidence_for_claim(claim)` — iddia için **Wikipedia API’den çekilen** metin.

Yani “hangi kanıta göre?” sorusunun cevabı: **O turda scriptin verdiği o tek `evidence` metni.** Commander’ın buna erişimi, kendisine parametre olarak gelen `evidence` (string) ve `evidence_embedding` (vektör) ile sınırlı.

**“Kanıtla ne kadar uyumlu” nasıl hesaplanıyor?**  
Commander kanıt metnini **anlamsal olarak yorumlamıyor** (NLI, mantık, çelişki kontrolü yok). Sadece **embedding benzerliği** kullanılıyor:

1. **evidence_embedding:** Referans kanıt metninin embedding’i (script `get_embeddings([evidence])[0]` ile üretip veriyor).
2. **agent_embedding:** İlgili ajan cevabının embedding’i (script tüm `responses` için embedding alıp veriyor).
3. **Uyum skoru:** `_evidence_alignment_score(agent_embedding, evidence_embedding)` = bu iki vektör arasındaki **cosine similarity**, [−1, 1]’den [0, 1]’e ölçeklenmiş hali.

Yani “kanıtla uyum” = **“ajan cevabı ile referans kanıt metni, embedding uzayında ne kadar yakın?”** — anlamca benzer cümleler genelde daha yüksek skor alır, ancak **mantıksal çelişki / destekleme** açıkça değerlendirilmez; sadece semantik yakınlık kullanılır. CHECK-MAS ise ayrıca claim + evidence + ajan metnini LLM ile değerlendirip BLOCK/PASS verir; bu, “kanıtla uyum”un Commander içindeki embedding-tabanlı hesabından farklı, anlama dayalı bir katman oluşturur.

---

### 6.3 "Spectral evidence-aware" nedir, ne yapacak?

**Şu an u (spectral) neye bakıyor?**  
Sadece **ajanların birbirine ne kadar benzer cevap verdiğine** bakıyor. Hesaplama kabaca şöyle: Her ajanın cevabı bir vektöre çevriliyor; "Ajan 1 ile Ajan 2 ne kadar benzer?", "Ajan 1 ile Ajan 3 ne kadar benzer?" … tüm çiftler için benzerlikler bir matrise yazılıyor. Bu matristen **u** çıkarılıyor: "çoğu ajanla benzer olan" ajanlar yüksek u alıyor, "tek başına kalan" ajanlar düşük u alıyor. Yani u = **"bu ajan kalabalığın (konsensüsün) içinde mi?"** skoru.

**Sorun nerede?**  
Konsensüs her zaman doğru değil. İki saldırgan (Mallory, Sybil) aynı yalanı yazarsa birbirine çok benzer olur → ikisi de yüksek u alır. Dürüst ajan (Alice) kanıta dayalı, farklı bir şey yazarsa "kalabalığa" benzemez → düşük u alabilir. Yani **u sadece "çoğunluğa benzerlik"e bakıyor; "kanıta uyum"a hiç bakmıyor.** Bu yüzden yanlış konsensüs de yüksek u ile ödüllendirilebiliyor.

**"Spectral evidence-aware" ile ne yapılacak?**  
u hesabına **kanıt (evidence)** da sokulacak. Yani sadece "ajan diğer ajanlara ne kadar benzer?" değil, **"ajan referans kanıt metnine ne kadar benzer?"** bilgisi de kullanılacak. Somut seçenekler:

- **Seçenek A:** u'yu şu anki gibi hesapla; sonra her ajan için **u'yu "kanıtla benzerlik" ile harmanla**. Kanıta yakın ajanların u'su yükselsin, kanıttan uzak olanların düşsün.
- **Seçenek B:** Benzerlik matrisini kurarken sadece ajan–ajan benzerliği kullanma; **ajan–kanıt benzerliğini de** (ör. ek bir sütun/satır veya ağırlık olarak) matrise kat; sonra u'yu bu yeni matristen hesapla. Böylece "kanıta yakın" ajanlar doğal olarak daha merkezî (yüksek u) çıkar.

**Özet:**  
Şu an u = "çoğunluğa benzer misin?". Evidence-aware u = "çoğunluğa benzer misin **ve** kanıta yakın mısın?". Amaç: Yanlış ama birbirine benzer iki ajanın sırf "kalabalık" oldukları için yüksek u almasını azaltmak; kanıta gerçekten yakın olan ajanın u'sunu yükseltmek.

---

### 6.4 "Çok tur oylama" nedir, neden lazım, ne zaman kullanılır?

**Şu an (tek tur) ne yapılıyor?**  
Bir kez: Ajanlar cevap veriyor → Commander pipeline çalışıyor → güven skorları (T) bir kez güncelleniyor → en yüksek güvenli ajanlar seçiliyor. Biter. İkinci bir "tur" yok: ajanlar tekrar konuşmuyor, güven tekrar güncellenmiyor.

**Çok tur oylama ne demek?**  
Birden fazla **tur**: Her turda ajanlar (yeniden veya ek) cevap üretir → pipeline çalışır → güven **bir önceki turun güveninden** devam ederek güncellenir → istenirse bir sonraki turda aynı ajanlar tekrar konuşur veya sadece yüksek güvenliler konuşur. Yani güven **zamanla / turlar boyunca** evrilir; tek seferlik değil, **tekrarlı** bir oylama/tartışma.

**Neden lazım?**  
- **Tartışma gerçekten birkaç adımdan oluşuyorsa:** Örn. 1. turda herkes fikrini söyler, 2. turda birbirine cevap verir, 3. turda son özet. Tek turda sadece "ilk cevaplar"ı görürsün; ikinci turdaki düzeltmeleri veya safsataları hesaba katmak için güveni tekrar güncellemek gerekir.  
- **Güveni yavaş yavaş netleştirmek istiyorsan:** İlk turda belirsiz kalabilir; ikinci turda yeni cevaplar veya ek kanıt gelince güveni yeniden hesaplamak mantıklı.  
- **Çok aşamalı karar:** Örn. 1. turda "güvenilir" kümesini seç, 2. turda sadece onlar tekrar konuşsun, son karar 2. turdan çıksın. Bunun için pipeline'ın birden fazla kez, önceki T'yi başlangıç alarak çalışması gerekir.

**Sürekli mi yapılacak?**  
Hayır. **Her senaryoda gerekmez.** Ne zaman **tek tur yeter:**  
- Tek seferlik bir soru + tek seferlik cevaplar (örn. bir iddia, bir set yorum, bir karar).  
- Maliyet / gecikme önemli: Her tur ek LLM/CHECK-MAS çağrısı demek; çoğu fact-checking veya içerik moderasyonu tek turda biter.  
- Doğal bir "ikinci tur" yok: Kullanıcı bir kez soruyor, ajanlar bir kez cevaplıyor, çıktı bir kez üretiliyor.

Ne zaman **çok tur düşünülür:**  
- **Gerçek tartışma protokolü:** Ajanlar birbirine cevap veriyor, birkaç raund konuşma var; her raund sonrası güveni güncellemek istiyorsun.  
- **İteratif iyileştirme:** Önce kaba filtreleme, sonra seçilenlerle ikinci tur (daha detaylı veya daha pahalı model).  
- **Zamanla gelen veri:** İlk turda az yorum var, sonra daha fazla yorum/kanıt geliyor; güveni yeni veriyle yeniden güncellemek istiyorsun.

**Özet:** Çok tur = güvenin **birden fazla adımda**, önceki turun sonucuna dayanarak yeniden hesaplanması. Sürekli yapılmaz; sadece **tartışmanın doğal olarak çok adımlı olduğu** veya **güveni turlar boyunca rafine etmek istediğin** durumlarda kullanılır. Tek tur, birçok uygulama (tek soru–tek cevap seti, fact-checking, tek seferlik moderasyon) için yeterli kalır.

**Kodda kullanım:** `run_multi_round(user_query, num_rounds, get_round_responses, evidence=..., claim=..., use_check_mas=...)`. `get_round_responses(round_index)` her tur için `(agent_responses, embeddings)` döndürmeli; ajan sayısı tüm turlarda aynı olmalı. Sentez, son turun cevapları ve güncel güven skorlarıyla üretilir.

---

## 7. "Zaten cevabı biliyoruz, neden tartıştırıyoruz?" — Gerçek dünya kullanımı ve makale

**Haklı soru:** Deneyde iddia (örn. "Roma 1453’te mi yıkıldı?") ve veri setindeki kanıt + ground_truth zaten var. Yani cevabı biliyoruz; ajanları bu iddia etrafında tartıştırıp Commander’a gönderiyoruz. Gerçek hayatta neden böyle bir motor kullanalım? Makale nasıl ses getirir?

### 7.1 Deneyde ne yapıyoruz (laboratuvar)

- **Amaç ölçmek:** Savunmanın **ne kadar işe yaradığını** ölçmek. Saldırgan (Mallory, Sybil) ve dürüst ajan (Alice) simüle ediliyor; kanıt ve ground truth **sadece değerlendirme için** kullanılıyor: "Commander doğru ajanı yükseltti mi, saldırganı düşürdü mü?"  
- Yani "1453’ü biliyoruz" kısmı **test için**. Gerçek hayatta motorun "cevabı bilmesi" gerekmez; deneyde bilmemizin sebebi, savunmanın kalitesini sayıyla (accuracy, BLOCK oranı vb.) ölçebilmek.

### 7.2 Gerçek projelerde nasıl kullanılır?

Gerçek hayatta çoğu zaman **kesin ground truth yok**; ama **referans kanıt** (metin, rapor, veritabanı çıktısı) vardır. Motor şunu yapar: "Verdiğin referans kanıta ve tartışma kurallarına göre hangi sesler uyumlu, hangileri safsata / manipülasyon kullanıyor?" — cevabı **üretmez**, **ajanları ağırlıklandırır**.

**Somut kullanım senaryoları:**

1. **Claim / iddia doğrulama (fact-checking)**  
   Sosyal medyada yeni bir iddia çıkıyor; siz "doğru mu?" bilmiyorsunuz. Sistem: (a) iddiayı alır, (b) **kanıtı siz üretirsiniz** (arama, Wikipedia, güvenilir haber arşivi, resmî kaynaklar — otomatik veya yarı-otomatik), (c) birden fazla ajan veya kaynak bu iddia + kanıt hakkında yorum üretir (LLM, insan özetleri, botlar), (d) Commander + CHECK-MAS: Kanıtla çelişen veya safsata kullanan sesleri düşürür, kanıta uyumlu ve tutarlı olanları öne çıkarır. **Çıktı:** Hangi seslere daha çok güvenileceği; nihai "evet/hayır" kararı yine insan veya ayrı bir karar modülüne bırakılabilir.

2. **Dezenformasyon / yanlış bilgi izleme**  
   Birden fazla analist veya bot bir iddiayı işaret ediyor; bazıları kötü niyetli veya yanıltıcı. Sizin elinizde **referans dokümanlar** (resmî açıklamalar, raporlar) var — mutlak doğru değil, ama "bu referansa göre hangi yorumlar uyumlu?" diye sormak anlamlı. Commander, referans kanıtı kullanarak hangi seslerin kanıtla uyumlu ve safsatasız olduğunu ağırlıklandırır; karar insan veya politika ile alınır.

3. **Uzman / danışman çakışması**  
   Birden fazla uzman veya danışman farklı öneriler veriyor; elinizde raporlar, veriler (evidence) var. Motor: "Verdiğim dokümanlara hangi uzman daha uyumlu, hangisi kaynağa saldırıyor veya mantık hatası yapıyor?" diye skorlar. Nihai karar yine insanda kalır; motor sadece **hangi seslere daha çok ağırlık verileceğini** önerir.

**Ortak nokta:**  
Motor **cevabı vermiyor**; "verdiğin kanıt ve tartışma kurallarına göre hangi ajanlar daha güvenilir?" diye **oylama / ağırlık** üretiyor. Kanıt sizin sistemin dışından gelir (arama, veritabanı, insan seçimi). Gerçek hayatta "1453’ü biliyoruz" yok; "şu referans metinleri kanıt kabul ediyoruz, buna göre filtrele" var.

### 7.3 Makalenin ses getirmesi için

- **Net çerçeve:** (1) Bu bir **saldırı–savunma değerlendirme çerçevesi**: Bilinen ground truth ile "manipülasyona dayanıklı oylama ve CHECK-MAS ile filtreleme ne kadar çalışıyor?" ölçülüyor. (2) **Gerçek dünya kullanımı** ayrı bir başlık: Kanıtın nasıl sağlandığı (retrieval, insan), hangi alanlar (fact-checking, dezenformasyon, karar destek), sınırlar (kanıt yanlışsa motor da yanılır; insan son karar verebilir).  
- **Ses getirmesi:** Savunma mimarisi (Φ, spectral, CHECK-MAS, evidence-aware), ölçülebilir deneyler ve gerçekçi sınırların açık yazılması makaleyi inandırıcı ve tekrarlanabilir yapar. "Neden zaten bildiğimiz bir şeyi tartıştırıyoruz?" sorusunu dokümanda ve makalede **bu bölümle** yanıtlamak, hem eleştiriyi önler hem gerçek projelere taşınabilirliği netleştirir.
