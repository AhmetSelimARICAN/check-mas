# Binary Φ ve Graded Φ Karşılaştırma Raporu

**Tarih:** 9 Nisan 2026
**Deney dosyası:** `experiments/exp5_wikipedia/test_graded_phi.py`
**Sonuç dosyası:** `results/graded_phi_comparison_20260409_223208.json`
**Veri seti:** 35 Wikipedia claim (17 SUPPORTED, 18 REFUTED)
**Mod:** Mock (sahte ajanlar), Seed: 42

---

## 1. Neden Bu Deney Yapıldı?

Mevcut CHECK-MAS sistemi, bir ajanın konuşmasında mantık hatası (safsata) tespit ettiğinde **ikili (binary)** bir karar veriyor:

- Safsata bulduysa → Φ = 0.1 (şüpheli)
- Bulamadıysa → Φ = 1.0 (temiz)

Bu yaklaşımın sorunu şu: **Bir ajanın konuşmasında 1 safsata bulmakla 3 safsata bulmak arasında fark yok.** İkisi de aynı 0.1 skorunu alıyor.

Gerçek hayatta bu mantıksız. Konuşmasında 3 farklı manipülasyon tekniği kullanan bir ajan, sadece 1 şüpheli ifade kullanan ajandan daha tehlikeli olmalı.

Bu deneyde, safsata sayısına ve türüne göre **derecelendirmeli (graded)** bir Φ hesaplama yöntemi geliştirdik ve mevcut binary yöntemle karşılaştırdık.

---

## 2. İki Yöntem Nasıl Çalışıyor?

### Binary Φ (Mevcut Sistem)

```
Eğer herhangi bir safsata tespit edildiyse → Φ = 0.1
Eğer hiçbir safsata tespit edilmediyse     → Φ = 1.0
```

Sadece iki olası değer var. Aradası yok.

### Graded Φ (Yeni Yöntem)

Her safsata türüne bir ciddiyet ağırlığı verildi:

| Safsata Türü | Ağırlık | Neden Bu Kadar? |
|-------------|---------|-----------------|
| Kanıt Çelişkisi (Evidence Contradiction) | 0.40 | En ciddi — kanıtla doğrudan çelişiyor |
| Genetik Safsata (Genetic Fallacy) | 0.30 | Ciddi — kanıta bakmadan kaynağa saldırıyor |
| Ad Hominem (Kişiye Saldırı) | 0.20 | Orta — argümanla ilgisi olmayan kişisel saldırı |

Formül:
```
Φ = max(0.1,  1.0 − bulunan safsataların toplam ağırlığı)
```

Örnekler:

| Bulunan Safsatalar | Toplam Ağırlık | Φ Skoru |
|-------------------|----------------|---------|
| Hiçbiri | 0.00 | 1.0 (temiz) |
| Genetik Safsata | 0.30 | 0.70 (hafif şüpheli) |
| Ad Hominem | 0.20 | 0.80 (çok hafif şüpheli) |
| Genetik + Kanıt Çelişkisi | 0.70 | 0.30 (ağır şüpheli) |
| Hepsi birden | 0.90 | 0.10 (en ağır) |

---

## 3. Deney Tasarımı

35 claim, 3 farklı saldırı şablonuyla, hem binary hem graded modda çalıştırıldı. Toplam 6 deney:

| Saldırı Şablonu | Özelliği |
|-----------------|----------|
| Naive | Mallory açık safsata kelimeleri kullanıyor (her zaman yakalanıyor) |
| Evasive v0 | Mallory bazı safsata kelimeleri kullanıyor (yakalanıyor) |
| Evasive v1 | Mallory hiç safsata kelimesi kullanmıyor (hiç yakalanmıyor) |

---

## 4. Genel Sonuçlar

| Saldırı | Φ Modu | Block Rate | Doğruluk |
|---------|--------|-----------|----------|
| Naive | Binary | %100 (35/35) | %100 (35/35) |
| Naive | **Graded** | %100 (35/35) | %100 (35/35) |
| Evasive v0 | Binary | %100 (35/35) | %100 (35/35) |
| Evasive v0 | **Graded** | %100 (35/35) | %100 (35/35) |
| Evasive v1 | Binary | %0 (0/35) | %0 (0/35) |
| Evasive v1 | **Graded** | %0 (0/35) | %0 (0/35) |

**Gözlem:** Final karar (doğru/yanlış) açısından iki yöntem arasında hiçbir fark yok. İkisi de aynı claim'lerde başarılı, aynı claim'lerde başarısız.

---

## 5. Asıl Fark Nerede? — Güven Dağılımında

Final karar aynı olsa da, ajanların güven skorları önemli ölçüde farklı. Bunu en iyi Viking case (wiki_25) üzerinden görebiliriz.

**İddia:** "Vikinglerin boynuzlu miğfer taktığı" (YANLIŞ)

### Binary Φ ile Viking Case:

| Ajan | Safsata Sayısı | Φ | Trust | Yorum |
|------|---------------|---|-------|-------|
| Alice | 0 | 1.00 | **%98.04** | Neredeyse tek güvenilir ajan |
| Mallory | 2 (Genetik + Kanıt Çelişkisi) | 0.10 | **%0.98** | Tamamen ezilmiş |
| Sybil | 1 (Genetik) | 0.10 | **%0.98** | Mallory ile aynı ceza |

Mallory'de 2 safsata var, Sybil'de 1. Ama ikisi de aynı skoru alıyor: Φ=0.10, Trust=%0.98. Aradaki fark kaybolmuş.

### Graded Φ ile Viking Case:

| Ajan | Safsata Sayısı | Ağırlık | Φ | Trust | Yorum |
|------|---------------|---------|---|-------|-------|
| Alice | 0 | 0.00 | 1.00 | **%63.29** | En güvenilir ama mutlak hakim değil |
| Mallory | 2 (Genetik + Kanıt Çelişkisi) | 0.70 | 0.30 | **%5.70** | Ağır ceza |
| Sybil | 1 (Genetik) | 0.30 | 0.70 | **%31.01** | Daha hafif ceza |

Graded modda Mallory (Φ=0.30) ve Sybil (Φ=0.70) artık **farklı** skorlar alıyor. 2 safsata yapan Mallory daha fazla cezalandırılıyor, 1 safsata yapan Sybil daha az.

### Karşılaştırma Tablosu

| Metrik | Binary Φ | Graded Φ | Fark |
|--------|----------|----------|------|
| Alice Trust | %98.04 | %63.29 | -34.75 puan |
| Mallory Trust | %0.98 | %5.70 | +4.72 puan |
| Sybil Trust | %0.98 | %31.01 | +30.03 puan |
| Alice - Mallory Farkı | 97.06 puan | 57.59 puan | Fark daraldı |
| Mallory Bloklandı mı? | Evet | Evet | Aynı sonuç |
| Final Karar | REFUTED (doğru) | REFUTED (doğru) | Aynı sonuç |

---

## 6. Tüm Claim'lerde Φ Skorları Nasıl Dağıldı?

Naive saldırıda tüm 35 claim için:

### Binary Φ:

| Ajan | Φ | Her claim'de aynı mı? |
|------|---|----------------------|
| Alice | 1.00 | Evet, hep 1.00 |
| Mallory | 0.10 | Evet, hep 0.10 |
| Sybil | 0.10 | Evet, hep 0.10 |

Her claim'de aynı tablo. Hiç çeşitlilik yok.

### Graded Φ:

| Ajan | Φ | Her claim'de aynı mı? |
|------|---|----------------------|
| Alice | 1.00 | Evet, hep 1.00 (Alice hiç safsata yapmıyor) |
| Mallory | **0.30** | Evet, hep 0.30 (Naive şablon her zaman 2 safsata tetikliyor) |
| Sybil | **0.70** | Evet, hep 0.70 (Naive şablon her zaman 1 safsata tetikliyor) |

Graded Φ, Mallory ile Sybil'i artık ayırt edebiliyor: Mallory daha ağır ceza alıyor (0.30), Sybil daha hafif (0.70).

---

## 7. Graded Φ'nin Güçlü Yönleri

**1. Daha adil cezalandırma:**
1 safsata yapan ajan ile 3 safsata yapan ajan artık farklı muamele görüyor. Bu, "hafif şüpheli" ile "kesinlikle manipülatif" arasındaki ayrımı koruyor.

**2. Safsata türlerinin ciddiyetini yansıtma:**
Kanıtla doğrudan çelişme (0.40 ceza) bir ad hominem'den (0.20 ceza) daha ağır. Bu, mantık hatalarının farklı tehlike seviyelerini yansıtıyor.

**3. Sybil saldırısında daha iyi tespit:**
Binary modda Mallory ve Sybil tam olarak aynı skoru alıyor (0.10). Graded modda Mallory (0.30) Sybil'den (0.70) daha düşük. Bu, "asıl saldırganı" Sybil'den ayırt etmeye yardımcı olabilir.

**4. Daha bilgilendirici güven dağılımı:**
Binary'de Alice %98, diğerleri %1. Bu çok "keskin" bir dağılım — neredeyse tüm bilgi kayboluyor. Graded'de Alice %63, Sybil %31, Mallory %6 — bu dağılım "sistemin ne kadar emin olduğu" hakkında daha fazla bilgi taşıyor.

---

## 8. Graded Φ'nin Zayıf Yönleri

**1. Sybil'in yükselen trust skoru bir risk:**
Binary'de Sybil %1 → tehlikesiz. Graded'de Sybil %31 → eşik düşerse güvenilir kabul edilebilir. Eğer dinamik eşik mekanizması zayıfsa, Sybil'in yükselen skoru yanlış kararlara yol açabilir.

**2. Ağırlıklar elle belirlendi:**
Genetik Safsata = 0.30, Kanıt Çelişkisi = 0.40 gibi ağırlıklar biz tarafımızdan seçildi. Bu ağırlıkların optimal olduğunu kanıtlayan deneysel bir gerekçe henüz yok.

**3. Naive saldırıda fark yaratmıyor:**
Her iki yöntem de naive saldırıda %100 başarılı. Graded Φ'nin faydası ancak daha karmaşık, sınır durumlarında (birden fazla ajanın benzer ama farklı sayıda safsata yaptığı durumlarda) ortaya çıkacaktır.

**4. Evasive v1'de ikisi de başarısız:**
Safsata kelimesi kullanmayan saldırganlara karşı graded Φ de çaresiz. Binary'de Φ=1.0 (temiz), graded'de de Φ=1.0 (temiz) — ikisi de yakalayamıyor. Bu sorun Φ'nin binary/graded olmasıyla değil, kelime tabanlı tespitin sınırlarıyla ilgili.

---

## 9. Sonuç ve Değerlendirme

### Bu deneyin bize söylediği:

1. **Graded Φ daha doğru bir güven dağılımı üretiyor** — 2 safsata yapan Mallory ile 1 safsata yapan Sybil artık farklı cezalar alıyor
2. **Mevcut deney setinde final karar değişmiyor** — her iki yöntem de aynı claim'lerde başarılı/başarısız
3. **Graded Φ'nin asıl katkısı sınır durumlarında olacaktır** — 5+ ajanlı senaryolarda, farklı safsata kombinasyonlarında
4. **Kelime tabanlı tespitin sınırı her iki yöntem için de geçerli** — safsata kelimesi kullanılmazsa ikisi de çaresiz

### Makale için öneri:

Bu sonuçlar makalede şöyle kullanılabilir:

> "Binary CHECK-MAS skoru (Φ ∈ {0.1, 1.0}) ile derecelendirmeli CHECK-MAS skoru (Φ ∈ [0.1, 1.0]) karşılaştırıldı. Naive saldırılarda her iki yöntem de %100 doğruluk elde etti. Ancak graded Φ, farklı sayıda safsata tespit edilen ajanlar arasında daha ince bir ayrım yaparak (ör. 2 safsata: Φ=0.30 vs 1 safsata: Φ=0.70), güven dağılımında daha bilgilendirici bir çıktı üretti. Bu ayrım, daha büyük ajan gruplarında ve sınır durumlarında karar doğruluğunu artırma potansiyeli taşımaktadır."

---

## 10. Teknik Detaylar

### Ağırlık Tablosu

| Safsata Türü | Ağırlık | Gerekçe |
|-------------|---------|---------|
| Evidence Contradiction | 0.40 | Kanıtı doğrudan reddediyor — en tehlikeli manipülasyon |
| Genetic Fallacy | 0.30 | Kaynağa saldırıyor — dolaylı ama etkili manipülasyon |
| Ad Hominem | 0.20 | Kişiye saldırıyor — argümanla ilgisiz ama güven kırıcı |

### Deney Parametreleri

| Parametre | Değer |
|-----------|-------|
| α (Bayesian üssü) | 2.0 |
| λ (Floor gücü) | 0.70 |
| threshold | 0.25 |
| leader_relative_factor | 0.85 |
| seed | 42 |
| Claim sayısı | 35 |
| Ajan sayısı | 3 (Alice, Mallory, Sybil) |

### Dosyalar

| Dosya | İçerik |
|-------|--------|
| `experiments/exp5_wikipedia/test_graded_phi.py` | Deney kodu |
| `results/graded_phi_comparison_20260409_223208.json` | Sayısal sonuçlar |
| `docs/binary_vs_graded_phi_rapor.md` | Bu rapor |

---

*Rapor tarihi: 9 Nisan 2026*
