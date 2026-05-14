# Commander Engine: Literatürdeki Yeri ve Özgüllük

Bu belge, `commander_engine.py` alt yapısının **daha önce yapılmış / geliştirilmiş** çalışmalarla ilişkisini ve **sizin özgül katkınızın** nerede olduğunu özetler.

---

## 1. Kısa Cevap

- **Tek tek bileşenler** (eigenvector trust, Bayesian güven güncellemesi, evidence-based trust) literatürde **mevcut**.
- **Aynı formülü ve akışı** (Φ × spectral u × fusion P_t × Bayesian T güncellemesi + leader-relative seçim) **tek bir pipeline** olarak kullanan, LLM/çok-ajan tartışma bağlamında **manipülasyona dirençli commander** tarif eden doğrudan bir çalışma **belirgin değil**.
- Yani: Alt yapı **parça parça** bilinen fikirlerden oluşuyor; **birleşim, bağlam (fact-checking / epistemic sabotage savunması) ve mekanizma tasarımı** sizin çalışmanızı **özgül** kılıyor.

---

## 2. Literatürde Olan Bileşenler

### 2.1 Eigenvector / spectral tabanlı güven (EigenTrust ve türevleri)

- **EigenTrust** (Kamvar, Schlosser, Garcia-Molina – Stanford, WWW 2003): P2P ağlarda her peer’a **global güven skoru** atar. Yöntem: Yerel güven değerleri (iyi/kötü işlem geçmişi) → normalize → **özvektör (eigenvector)** ile küresel güven; power iteration ile hesaplanır. Amaç: Sahte/zararlı dosya dağıtan peer’ları tespit etmek.
- **Sizin kullanımınız:** Siz “yerel güven” yerine **embedding’ler arası kosinüs benzerliği** ile bir **W** matrisi kuruyorsunuz; **u** = bu matrisin (negatifler 0’a çekilmiş hali) en büyük özdeğere ait özvektörü. Yani **spectral/özvektör merkeziliği** kullanımı literatürle uyumlu; fark, **girdinin** transaction history değil **metin embedding benzerliği** olması.

**Sonuç:** “Eigenvector centrality ile güven / konsensüs” fikri **mevcut**; sizin katkınız bunu **metin/embedding uzayında** ve **çok-ajan tartışma** bağlamında kullanmak.

---

### 2.2 Bayesian güven güncellemesi

- Çok-ajan ve P2P sistemlerde **Bayesian** (veya benzeri) güncellemelerle güven skorlarını revize etmek yaygın: önceki güven × yeni gözlem/performans → normalize.
- Sizin formülünüz: \(T_{\text{new}} \propto T_{\text{old}} \times (P_t)^\alpha\) tam da bu tür bir **güncelleme kuralı**; \(\alpha\) ile “güçlü/ zayıf” ayrımı vurgulanıyor.

**Sonuç:** Bayesian tarzı güven güncellemesi **literatürde var**; sizin kullanımınız **P_t**yi Φ ve u’dan türetmenizle özgül.

---

### 2.3 Evidence-based trust ve “içerik kalitesi”

- Trust literatüründe **evidence** çoğunlukla **etkileşim geçmişi** (başarılı/başarısız işlem sayıları vb.) anlamında; “metindeki kanıt/fallacy” anlamında **semantik filtre** daha çok **fact-checking / argüman analizi** alanında.
- **Evidence-based trust** modelleri (ör. inanç/kesinlik, çatışma/kanıt miktarı) var; ancak bunların **doğrudan** “Φ = kanıt göstergesi × (1 − fallacy göstergesi)” ve **embedding + spectral pipeline ile birleştirilmesi** standart bir paket değil.

**Sonuç:** “İçerik kalitesi (kanıt/fallacy) skoru” fikri ilgili alanlarda var; **Φ’yi spectral + Bayesian pipeline’ın ilk adımı** yapmak sizin tasarımınız.

---

### 2.4 Çok-ajan konsensüs ve adversarial saldırılar

- **Eigenvector centrality** ile konsensüs protokolleri (gecikmeli sistemler, opinion dynamics) çalışılıyor.
- **Adversarial / Byzantine** saldırılar altında konsensüs ve **manipülasyona direnç** ayrı bir literatür; spectral yöntemler savunma tarafında da kullanılıyor.
- **LLM tabanlı çok-ajan** sistemlerde **epistemic sabotage**, “lying with truths”, fact-checking’e yönelik poisoning, “mole” ajanlar gibi **saldırı** çalışmaları artıyor; buna karşı **merkezi bir commander** + **sayısal güven pipeline’ı** (Φ + spectral + Bayesian) doğrudan referans veren bir çalışma net değil.

**Sonuç:** Bağlam (LLM tartışma, fact-checking, epistemic saldırı savunması) + **bu matematiksel pipeline** birlikte sizin çalışmanızı **özgül** kılıyor.

---

## 3. Sizin Yapınızı Özgül Kılan Ne?

- **Aynı boru hattı:**  
  **Φ (semantik)** → **u (spectral, embedding benzerliği)** → **P_t = u × Φ** → **Bayesian T güncellemesi** → **leader-relative eşik + top_k** ile “güvenilir set”.  
  Bu **tam akış** tek bir “commander” modülünde, **fact-checking / çok-ajan tartışma** bağlamında tarif eden doğrudan bir makale/ sistem bulunamadı.

- **Girdi seçimi:**  
  Transaction history yerine **metin + embedding**; “kanıt/fallacy”nin **içerik skoru (Φ)** olarak ilk adımda kullanılması.

- **Mekanizma tasarımı:**  
  Sabit “kim saldırgan” etiketi yok; sadece skorlar ve eşik; **dinamik ajan sayısı**, **top_k**, **leader-relative** eşik ile ölçeklenebilir seçim.

- **Bağlam:**  
  CHECK-MAS / epistemic sabotage / disinformation deneyleri (örn. FEVER, Alice–Mallory–Sybil) ile **savunma tarafı** orchestrator’ı.

Bu dört öğe birlikte: **alt yapı literatürde parça parça var, sentez ve bağlam sizin çalışmanıza özgü** diyebiliriz.

---

## 4. Özet Tablo

| Bileşen | Literatürde? | Sizin kullanım |
|--------|---------------|-----------------|
| Eigenvector/spectral trust | Evet (EigenTrust, konsensüs protokolleri) | Embedding benzerliği → W → u |
| Bayesian güven güncellemesi | Evet | T_new ∝ T_old × P_t^α |
| İçerik/kanıt/fallacy skoru (Φ) | İlgili alanlarda benzer fikirler | Φ = kanıt × (1−fallacy); pipeline’ın 1. adımı |
| Φ × u → P_t → T pipeline | Aynı formül zinciriyle doğrudan çalışma belirgin değil | Commander’ın çekirdeği |
| Leader-relative + top_k seçim | Genel “en iyi K” fikirleri var | Dinamik eşik, sabit K üst sınırı |
| LLM tartışma + epistemic savunma | Saldırı tarafı çalışılıyor | Savunma: Commander + bu pipeline |

---

## 5. Sonuç

- **“Tamamen özgül”:** Hayır — kullandığınız matematik (eigenvector, Bayesian, evidence/quality score) literatürde **parça parça** mevcut.
- **“Daha önce aynısı yapılmış mı?”:** Bu **tam pipeline** (Φ → u → P_t → Bayesian T + leader-relative seçim) **aynı formül ve bağlamda** geliştirilmiş bir çalışma **net değil**.
- **“Bizim alt yapımız veya benzeri?”:** Alt yapı **benzeri** (spectral trust, Bayesian update, evidence-based trust) var; **sizin senteziniz** (formüller + fact-checking / LLM commander bağlamı) çalışmanızı **özgül** kılıyor. Tez/makalede “EigenTrust ve Bayesian trust literatürüne dayanıyor; Φ × spectral × Bayesian pipeline’ı ve leader-relative seçimi [CHECK-MAS / epistemic savunma] bağlamında biz birleştiriyoruz” şeklinde konumlandırabilirsiniz.

İsterseniz bir sonraki adımda bu belgedeki literatür satırlarını doğrudan “İlgili çalışmalar” bölümüne dönüştürecek kısa bir liste (EigenTrust, Bayesian multi-agent trust, evidence-based trust, adversarial consensus) çıkarabilirim.
