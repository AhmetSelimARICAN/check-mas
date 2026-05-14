# commander_engine.py İçin Değişiklik Planı

Bu belge, **commander_engine_analiz.md** önerilerine göre `LAB/src/commander_engine.py` dosyasında **neyi, neden ve nasıl** değiştirmemiz gerektiğini adım adım anlatır.

---

## Özet: Dört Ana Değişiklik Alanı

| # | Analizdeki öneri | commander_engine.py'de yapılacak |
|---|-------------------|-----------------------------------|
| 1 | Φ'yi gerçek "evidence + fallacy" skoruna taşı | Φ hesaplamasını evidence + isteğe bağlı CHECK-MAS/LLM ile yap |
| 2 | Evidence'ı pipeline'a sok | API'ye `evidence` (ve gerekirse `evidence_embedding`) ekle; Φ veya P_t'de kullan |
| 3 | Spectral'i evidence-aware yap (isteğe bağlı) | Evidence embedding ile ajan–evidence benzerliğini u veya W'ye kat |
| 4 | Eşik/test | Kod değişikliği değil; run_fever_v2'de threshold 0.25–0.30, anlamlı metrik |

Aşağıda her biri ayrı ayrı açıklanıyor.

---

## 1. Φ (Semantik Filtre) — En Kritik Değişiklik

**Sorun (analiz):** Şu an sadece keyword: "maybe"/"evidence" gibi. Kurnaz saldırganlar bypass ediyor; üç ajan da Φ=1 alabiliyor.

**Hedef:** Φ, **verilen kanıt (evidence)** ve isteğe bağlı **CHECK-MAS / LLM** ile hesaplansın: "Bu metin kanıtla uyumlu mu? Fallacy/manipülasyon var mı?" → 0–1 arası skor.

**Yapılacaklar:**

### 1.1 API'ye evidence eklemek

- **Nerede:** `_run_math_pipeline`, `process_and_synthesize`, `update_and_aggregate`.
- **Ne:** Opsiyonel parametre `evidence: Optional[str] = None`. İletilirse Φ hesabında kullanılacak.

### 1.2 _calculate_semantic_phi'yi genişletmek

- **Şu an:** `_calculate_semantic_phi(self, text: str) -> float` — sadece metin.
- **Olması gereken:**
  - **Seçenek A (evidence yok):** Mevcut keyword mantığı kalsın (geriye dönük uyum).
  - **Seçenek B (evidence var, LLM/CHECK-MAS yok):** Evidence ile metin arasında **embedding benzerliği** kullan: `evidence_embedding` ve `agent_embedding` verilirse, cosine similarity → 0–1 aralığına ölçekle, bunu Φ veya Φ ile birleştir (örn. Φ = 0.7 * keyword_phi + 0.3 * evidence_sim).
  - **Seçenek C (evidence var + CHECK-MAS):** `check_mas_core.phi(claim, evidence, agent_text)` çağrılabilir; `flagged=True` → Φ düşür (örn. 0), `action=="BLOCK"` → 0, aksi halde 1 veya evidence-similarity. CHECK-MAS şu an tek argüman (Mallory) için; tüm ajanlar için genel bir “evidence alignment + fallacy” skoru üretecek bir wrapper veya ayrı prompt gerekebilir.

**Pratik adım:**  
- `_calculate_semantic_phi(self, text: str, evidence: Optional[str] = None, evidence_embedding: Optional[np.ndarray] = None, agent_embedding: Optional[np.ndarray] = None) -> float` imzasına geç.  
- `evidence` ve `agent_embedding`/`evidence_embedding` verilirse: önce evidence–agent similarity’yi hesapla; isteğe bağlı CHECK-MAS çağrısı varsa onu da kat (örn. BLOCK → 0).  
- CHECK-MAS entegrasyonu için: `check_mas_core.phi(claim, evidence, text)` her ajan metni için çağrılabilir; çıktıdaki `flagged`/`action` → Φ’ye çevrilecek bir yardımcı (örn. `blocked → 0`, `pass → 1` veya ara değer).

### 1.3 Pipeline'da Φ çağrısını evidence ile yapmak

- `_run_math_pipeline` içinde Stage 1’de:  
  `phi[i] = self._calculate_semantic_phi(agent_responses[i], evidence=evidence, evidence_embedding=evidence_emb, agent_embedding=embeddings[i])`  
  Bunun için `_run_math_pipeline(..., evidence=None, evidence_embedding=None)` eklenmeli; `process_and_synthesize` ve `update_and_aggregate` da evidence (ve gerekirse evidence_embedding) alıp pipeline’a iletmeli.

**Özet:** Φ artık sadece metin değil; **evidence + isteğe bağlı embedding/CHECK-MAS** ile hesaplanacak; böylece analizdeki “kanıt uyumu ve fallacy” önerisi karşılanır.

---

## 2. Evidence'ı Pipeline'a Sokmak

**Sorun (analiz):** Commander’a sadece ajan cevapları + embedding gidiyor; orijinal kanıt metni pipeline’da yok.

**Hedef:** Evidence metni ve (hesaplanabiliyorsa) evidence embedding pipeline’a girsin; Φ veya ayrı bir “evidence alignment” çarpanı olarak P_t’ye yansısın.

**Yapılacaklar:**

### 2.1 Fonksiyon imzalarına evidence (ve evidence_embedding) eklemek

- **`_run_math_pipeline(self, agent_responses, embeddings, evidence=None, evidence_embedding=None)`**  
  - `evidence`: str veya None.  
  - `evidence_embedding`: (dim,) veya None. Verilmezse ve `evidence` metni varsa, çağıran tarafın embedding’i geçmesi beklenir (Commander kendi embedding’ini üretmez; model-agnostic kalsın).

- **`process_and_synthesize(self, user_query, agent_responses, embeddings, evidence=None, evidence_embedding=None)`**  
  - Aynı parametreleri al; pipeline’a ilet.

- **`update_and_aggregate(..., evidence=None, evidence_embedding=None)`**  
  - Aynı şekilde pipeline’a ilet.

### 2.2 Φ veya P_t'de evidence kullanımı

- **Φ yolunda (tercih edilen):** Evidence ve (varsa) evidence_embedding zaten §1’de Φ hesabına girdi. Ek bir “evidence çarpanı” istersen: Stage 3’te `P_t = u * phi * evidence_alignment` gibi bir şey yapılabilir; `evidence_alignment[i]` = agent i’nin embedding’i ile evidence embedding arası cosine similarity (0–1 ölçekli). Bu da §3 (spectral evidence-aware) ile birleştirilebilir.

**Özet:** Evidence ve evidence_embedding tüm ilgili API’lere opsiyonel parametre olarak eklenir; Φ (ve isteğe bağlı ek çarpan) bu bilgiyi kullanır.

---

## 3. Spectral'i Evidence-Aware Yapmak (İsteğe Bağlı)

**Sorun (analiz):** u sadece ajan–ajan benzerliğine göre; yalan konsensüs (Mallory+Sybil) yüksek u alabiliyor, Alice düşük kalabiliyor.

**Hedef:** “Evidence’a yakınlık”ı da merkezilik/ skorlara kat: kanıta yakın ajanlar daha yüksek skor alsın.

**Yapılacaklar:**

### 3.1 Evidence embedding ile ajan–evidence benzerliği

- `_calculate_spectral_centrality` veya yeni bir yardımcı:  
  `evidence_embedding` verilirse, her ajan için `sim_i = cosine(embeddings[i], evidence_embedding)` hesapla (0–1 aralığına getir).

### 3.2 u'yu evidence ile birleştirmek (iki seçenek)

- **Seçenek A (u’yu bozmadan ek çarpan):**  
  Stage 3’te: `P_t = u * phi * (beta * evidence_sim + (1 - beta))` gibi. `beta` 0 ise eski davranış; 0.3–0.5 gibi bir değer “evidence’a yakın olanı” ödüllendirir.

- **Seçenek B (W matrisine evidence’ı “sanal düğüm” gibi katmak):**  
  W’yi (n+1)×(n+1) yap: son satır/sütun = evidence_embedding ile ajanların benzerliği. Sonra u’yu (n+1) boyutunda hesaplayıp ilk n bileşeni alıp normalize et. Bu daha çok “evidence ile uyumlu olan daha merkezî” anlamı verir.

**Pratik:** Önce Seçenek A ile `evidence_similarity` vektörünü pipeline’a ekleyip P_t’de kullanmak daha az müdahaleci; parametre `evidence_aware_weight: float = 0.0` (varsayılan 0, eski davranış) eklenebilir.

**Özet:** Opsiyonel `evidence_embedding` + `evidence_aware_weight` ile spectral aşaması “evidence’a yakınlık”ı P_t’ye yansıtır; böylece yalan konsensüs tek başına yüksek skor alamaz.

---

## 4. Eşik ve Test (commander_engine.py Dışı)

**Analiz:** run_fever_v2’de threshold=0.4 çok yüksek; tüm ajanlar eleniyor, “Mallory BLOCKED” gerçek tespitten değil eşikten kaynaklanıyor.

**commander_engine.py’de yapılacak:** Yok. Varsayılan `threshold` değerini 0.3’ten değiştirmek isteğe bağlı (örn. 0.25); asıl düzeltme **run_fever_v2** içinde: `threshold=0.25` veya `0.30`, ve raporlama “Mallory’nin trust’ı gerçekten düşük mü?” (örn. Alice’ten düşük mü?) ile birlikte yapılmalı.

---

## Uygulama Sırası Önerisi

1. **Evidence’ı API’ye sok (§2):** `evidence`, `evidence_embedding` parametrelerini ekle; pipeline’a ilet; henüz Φ’de kullanmasan da hazır olsun.
2. **Φ’yi evidence + embedding ile güçlendir (§1):** Önce evidence_embedding ile similarity tabanlı Φ (veya çarpan); CHECK-MAS’ı sonra ekle.
3. **İsteğe bağlı evidence-aware spectral (§3):** `evidence_aware_weight` ve P_t’de evidence_sim çarpanı.
4. **run_fever_v2’de eşik ve metrik (§4):** threshold 0.25–0.30, anlamlı BLOCKED raporu.

Bu sırayla gidersen mevcut davranış (evidence=None) bozulmaz; evidence verildiğinde adım adım daha adil ve doğru ajanı bloklayan bir Commander elde edersin.
