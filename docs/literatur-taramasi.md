# Literatur Taramasi ve Kavramsal Konumlandirma

Bu belge, bildiri icin yapilan literatur taramasini ve en onemlisi
**projeyi hangi kavramla adlandiracagimiz** sorusunun cevabini kaydeder.

> **Durum:** Devam ediyor. Semantic Scholar anonim erisimde hiz sinirina
> takiliyor; derinlestirmek icin API anahtari ya da daha yavas tempo gerekli.

---

## 1. Kavram Secimi -- "Dijital Ikiz" Diyebilir miyiz?

**Kisa cevap: HAYIR.** Ve bunu bilerek yaziyoruz, cunku "digital twin"
bildirilerde en cok suistimal edilen terimlerden biri; alani bilen bir
hakem yanlis kullanimi ilk sayfada yakalar.

### Referans tanimlar

Barbie & Hasselbring (2024), *"From Digital Twins to Digital Twin
Prototypes: Concepts, Formalization, and Applications"*, arXiv:2401.07985
kavramlari Object-Z ile formalize ediyor. Ilgili tanimlar:

**Definition 7 -- Digital Model**
> "A digital model describes an object, a process, or a complex
> aggregation. The description is either a mathematical or a
> computer-aided design (CAD)."

**Definition 10 -- Digital Shadow**
> "...The connection from a physical twin to its digital shadow is
> **automated**. Changes on the physical twin are reflected to the digital
> shadow automatically. Vice versa, the digital shadow does not change the
> state of the physical twin."

**Definition 11 -- Digital Twin**
> "...connected to the physical twin over the entire life cycle for
> **automated bidirectional data exchange**, i.e. changes made to the
> digital twin lead to adapted behavior of the physical twin and
> vice-versa."

**Definition 12 -- Digital Twin Prototype (DTP)**
> "A Digital Twin Prototype (DTP) is the software prototype of a physical
> twin. **The configurations are equal**, yet the connected
> sensors/actuators are emulated. To simulate the behavior of the physical
> twin, the emulators use **existing recordings** of sensors and actuators.
> For continuous integration testing, the DTP can be connected to its
> corresponding digital twin, **without the availability of the physical
> twin**."

### Bizim konumumuz

| Kavram | Sart | Bizde var mi? |
|---|---|---|
| Digital Twin | Otomatik CIFT YONLU veri alisverisi | ❌ Hicbir baglanti yok |
| Digital Shadow | Otomatik TEK YONLU (fiziksel -> dijital) | ❌ Otomatik akis yok |
| Digital Twin Prototype | Cihazin KENDI yazilimi + emule sensorler | ⚠️ Kismen (asagiya bakiniz) |
| **Digital Model** | Matematiksel tanim | ✅ **Tam olarak buyuz** |

Simulator ile gercek cihaz birbirini HIC etkilemiyor: kayitlari elle
aldik, modeli elle kurduk. Cihaz degisse simulator kendiliginden
guncellenmez. Bu, tanim geregi Digital Model'dir.

### DTP ile aramizdaki KRITIK fark

DTP tanimindaki *"The configurations are equal"* ifadesi sunu varsayar:
**elinizde cihazin KENDI gomulu yazilimi vardir**, siz sadece sensorleri
emule edersiniz. Yani DTP yaklasimi CIHAZI GELISTIREN ekip icindir.

Bizde firmware yok. Biz cihazi DISARIDAN, protokol sinirindan gozlemleyip
davranisini yeniden urettik (black-box). Yani:

| | Barbie'nin DTP'si | Bizimki |
|---|---|---|
| Calisan yazilim | Cihazin GERCEK firmware'i | Bagimsiz yeniden yazim |
| Emule edilen | Sensorler/aktuatorler | Cihazin TAMAMI |
| Kim kullanir | Cihazi GELISTIREN | Cihazi KULLANAN |
| Erisim varsayimi | Kaynak koda erisim | Sadece kilavuz + protokol kaydi |

### Ortak yanlarimiz (ve bunlar cok)

DTP ile AMAC ve MIMARI olarak ortusuyoruz:
- Fiziksel cihaz olmadan yazilim testi ✅
- CI/CD hattinda otomatik entegrasyon testi ✅ (GitHub Actions + PTY)
- Davranisi GERCEK KAYITLARDAN turetmek ✅ (docs/gercek-cihaz-ciktilari.md)
- Protokolu OSI host katmaninda tutmak, surucuyu degistirmemek ✅

Bu sonuncusu ozellikle carpici: Barbie'nin bildirisi §3.7.1'de aynen
"communication protocols such as **RS232** need to stay on the host layers
of the OSI-Model without the need of changing the original connection
properties of a device driver" diyor. Bizim socat/PTY yaklasimimiz tam
olarak budur.

### SONUC -- kullanacagimiz dil

- ❌ "Dijital ikiz gelistirdik" **DEMEYECEGIZ**
- ✅ "Cihazin bir **dijital modeli**" diyecegiz
- ✅ DTP'yi **ilgili calisma** olarak konumlandiracagiz: ayni amac, farkli
  kisit
- ✅ Yazilim testi terminolojisinde bu bir **test ikizi (test double)**,
  daha dar tanimla bir **fake**: basitlestirilmis ama CALISAN bir
  gerceklestirim

---

## 2. Bulunan Bosluk

Iki literatur var ve birbirlerine degmiyorlar:

**A) Zamanlama / osilator literaturu** (PTTI, IEEE T-IM, EFTF/IFCS,
IET Radar): holdover modelleme cok gelismis -- Kalman filtresi, LSSVM,
DAC kuantizasyon gurultusu, spoofing altinda holdover sinirlari...
**Ama yazilim testi icin simulator derdi yok.**

**B) DTP / dijital ikiz literaturu** (cs.SE): donanimsiz CI testi
kavramsal olarak cozulmus, ama ornekler okyanus gozlem sistemleri, akilli
tarim, uretim hatlari. **Hassas zamanlama cihazi ornegi yok. Ayrica
ucuncu-taraf TICARI cihaz senaryosu yok** -- hep cihazi gelistiren ekip
varsayiliyor.

### Bizim doldurdugumuz bosluk

> Ucuncu-taraf ticari bir olcum cihazinin yerine gecebilecek, FIZIKSEL
> OLARAK ANLAMLI bir test ikizi; yalnizca (a) uretici kilavuzu ve
> (b) sinirli sayida protokol kaydi kullanilarak nasil kurulur -- ve
> sadakati, cihaza erisim KISITLIYKEN nasil dogrulanir?

Bu, endustride yaygin bir durum: cihazi satin alirsin, firmware'ine
erisemezsin, cihaz da surekli elinin altinda degildir.

**Literatur bu boslugu ISMIYLE onayliyor:** Khedr vd. (arXiv:2608.28498)
dijital ikiz muhendisliginde "relevance, verifiability, **substitutability**
and **fidelity**" niteliklerinin nasil BICIMLENDIRILIP DOGRULANACAGINA dair
pratik rehber olmadigini soyluyor. Bizim bildirimiz tam bu iki nitelik
uzerine somut, calisan bir ornek sunuyor: sinirli veriyle kurulan bir test
ikizinin YERINE GECEBILIRLIGINI ve SADAKATINI nasil gosterirsin.

---

## 3. Kaynakca (buyuyecek)

### Dijital ikiz / DTP / yazilim testi
- Barbie, A. & Hasselbring, W. (2024). *From Digital Twins to Digital Twin
  Prototypes: Concepts, Formalization, and Applications.* arXiv:2401.07985
  — **ANA REFERANS**, kavram tanimlari buradan
- Barbie, A., Hasselbring, W. & Hansen, M. (2023). *Enabling Automated
  Integration Testing of Smart Farming Applications via Digital Twin
  Prototypes.* arXiv:2311.05748
- Barbie, A. & Hasselbring, W. (2024). *Toward Reproducibility of Digital
  Twin Research: Exemplified with the PiCar-X.* arXiv:2408.13866
  — yeniden uretilebilirlik tartismasi icin

### GNSDO / holdover / zamanlama
- *Optimal Oscillator Modelling for GNSS-Disciplined Clock Holdover.*
  PTTI 2025
- *Global Navigation Satellite Systems disciplined oscillator
  synchronisation of multistatic radar.* IET Radar, Sonar & Navigation
  (2023) — holdover'da baslangic frekans ofsetinin baskin oldugunu
  gosteriyor; bizim y0 tercihimizi destekler
- *Enhancing GNSS timing and positioning performance through receiver
  clock noise modeling.* Measurement Science and Technology (2026)
  — Allan varyansi ile difuzyon katsayisi iliskisi
- *A Hybrid KF-LSSVM Clock Holdover Framework for NTN IoT
  Synchronization.* ICICC 2026
- *Over-the-Air Jamming and Spoofing Tests of GNSS Timing Devices.*
  EFTF/IFCS 2023 — jamming/HEALTH davranisi icin baglam

### Test ikizi / mock / dogrulama (YENI -- cekirdek katkiyi destekliyor)
- Tiwari, D., Monperrus, M. & Baudry, B. (2023). *RICK: Generating Mocks
  from Production Data.* arXiv:2302.04547
  — **GUCLU PARALEL.** Test double davranisini, gercek uygulamanin
  KAYITLARINDAN turetir: "observes executing applications... Based on the
  data collected from these observations, RICK produces unit tests with
  mocks, stubs." Bizim yaptigimizin ta kendisi -- onlar OTOMATIK, uygulama
  izlerinden; biz ELLE, cihaz protokol kayitlarindan. Yontem ayni: "gercek
  seyin kaydindan test ikizi uret."
- Khedr, M.T. vd. (2026). *A System-of-Systems Case Study for the
  Verification of Composed Digital Twins.* arXiv:2608.28498
  — **BOSLUGU ISMIYLE SOYLUYOR:** "lack practical guidance on how qualities
  such as relevance, verifiability, **substitutability** and **fidelity**
  may be formalised and verified." Bizim bildirinin merkezi tam bu iki
  nitelik: YERINE GECEBILIRLIK (substitutability) ve SADAKAT (fidelity).
- Waters, G. (2025). *Testing, Evaluation, Verification and Validation
  (TEVV) of Digital Twins: A Comprehensive Framework.* arXiv:2507.04555
- Mertens, J. & Denil, J. (2025). *Reusing Model Validation Methods for the
  Continuous Validation of Digital Twins of Cyber-Physical Systems.*
  arXiv:2512.04117
- Barbie, A., Hasselbring, W. & Hansen, M. (2023). *Enabling Automated
  Integration Testing of Smart Farming Applications via Digital Twin
  Prototypes.* arXiv:2311.05748

### GNSDO / holdover / zamanlama (ek)
- Peil, S., Akin, T.G. & Whalen, J.D. (2025). *100-ns-level timing holdover
  after 12 years for rubidium atomic fountains.* arXiv:2508.13140
  — holdover'da ns-seviye hata birikiminin uzun-vade karakteri
- Engelhardt, M. vd. (2026). *A Road-Mobile GNSS-Disciplined Oscillator...*
  arXiv:2604.24060 — hareketli GNSSDO, g-duyarlilik (bizim GYRO baglamimiz)

### AYRIM NOTU -- "GNSS simulator" bizim isimiz DEGIL
- Kim, W. & Seo, J. (2023). *Low-Cost GNSS Simulators with Wireless Clock
  Synchronization for Indoor Positioning.* arXiv:2306.00633
  — DIKKAT: bu bir SINYAL simulatoru (RF uydu sinyali uretir). Bizimki bir
  CIHAZ/PROTOKOL simulatoru (SCPI cevabi uretir). Terminoloji karismasin
  diye bildirimizde bu ayrimi acikca yapmaliyiz: "GNSS simulator" literaturu
  bize benzemez.

### Otomatik test ekipmani
- *A Holistic Approach to Hardware Abstraction Layers.* IEEE AUTOTESTCON
  2022 — "simulate systems without a need for physical instrumentation"

---

## 4. Onemli Uyari -- Katki Iddia ETMEYECEGIMIZ Yer

Holdover modelimiz `x(t) = x0 + y0*t + (D/2)*t^2` **ders kitabi
seviyesindedir** (standart iki-durumlu saat modeli). Literaturde bunun
uzerine Kalman filtresi, makine ogrenmesi, kuantizasyon gurultusu
modelleri kurulmus durumda.

**Buradan katki iddia edersek bildiri hakli olarak reddedilir.**

Modeli, katki olarak degil, "bilinen bir modeli belgelenmis parametrelerle
uyguladik" diye sunacagiz. Katkimiz modelin KENDISI degil, onu SINIRLI
VERIYLE KURMA ve DOGRULAMA yontemidir.
