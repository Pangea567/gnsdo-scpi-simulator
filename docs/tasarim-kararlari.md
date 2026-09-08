# Tasarim Kararlari ve Modelleme Notlari

Bu dosya, simulatoru gelistirirken **neyi neden** yaptigimizi kaydeder.
Amac: aylar sonra (ya da bildiriyi yazarken) geri donup baktigimizda
"burada niye boyle yapmisiz?" sorusuna cevap bulabilmek.

Her karar su formatta yazilir:
- **Durum**: ne problemle karsilastik
- **Karar**: ne yaptik
- **Neden**: gerekcesi, ve hangi belgeye dayaniyor
- **Alternatif**: neyi reddettik ve nicin

---

## 0. Temel Kavramlar (once bunlari anlamak lazim)

### 1PPS nedir?
Saniyede bir defa gelen bir elektriksel darbe ("one pulse per second").
Zaman referansi dagitmanin standart yolu. Darbenin yukselen kenari
"iste tam su an yeni saniye basladi" demektir.

### Cihazda KAC TANE 1PPS var? -> Iki tane
1. **GNSS alicisinin 1PPS'i**: uydulardan turetilir, UTC'ye baglidir.
   - Uzun vadede kusursuz (dunyanin zaman referansi)
   - Kisa vadede gurultulu (onlarca ns jitter; atmosfer, uydu geometrisi)
2. **Rubidyum osilatorun 1PPS'i**: cihazin kendi 10 MHz'ini 10 milyona
   bolerek uretilir.
   - Kisa vadede cok sakin (atomik gecis frekansina kilitli)
   - Uzun vadede kayar (yaslanma, sicaklik)

Ikisi birbirini tamamlar. Cihazin butun marifeti bu ikisini birlestirmek:
GNSS'in uzun vade dogrulugunu, Rubidyum'un kisa vade sessizligiyle.

### TINT nedir?
**TINT = Time INTerval** = yukaridaki iki 1PPS darbesi arasindaki zaman farki.

- Kilavuz §3.6.6: "the difference or Time Interval between the Rubidium or
  filter oscillator 1PPS output and the loop reference"
- Cozunurluk: **1E-10 saniye** (0.1 ns)
- Olcum donanimi: 20 ps cozunurluklu uclu zaman-aralik sayaci (§1.1)

TINT tek bir sayidir ama isleyisi anlamak icin sunu bilmek gerekir:
**TINT, kontrol dongusunun HATA SINYALIDIR.** Cihazin tum isi TINT'i
sifira yakin tutmaktir.

Benzetme: iki kol saati. Biri radyo sinyaliyle kendini ayarlayan (GNSS),
digeri cok kaliteli mekanik (Rubidyum). TINT = "su an ikisi arasinda kac
nanosaniye fark var?"

### Holdover nedir?
GNSS sinyali kesilince cihaz, son bildigi dogru frekansi kullanarak
"kendi basina yurumeye" devam eder. Kilavuzun kendi kelimesiyle: *coasting*
(§3.6.1). Bu sirada duzeltme gelmedigi icin hata **birikir**. Bu projenin
FAZ 1 hedefi tam olarak bu birikimi modellemek.

---

## 1. Olaylarin Akisi (sebep-sonuc)

### Kilitli calisma (kapali dongu)

    GNSS 1PPS ──┐
                ├──► TINT olculur ──► servo dongu ──► Rb frekansi ince ayarlanir
    Rb 1PPS ────┘         ▲                                    │
                          └────────────────────────────────────┘
                                 KAPALI DONGU: TINT -> 0

Sonuc: TINT 0.2 ns'nin altinda tutulur (§1.1: "better than 0.2ns average
phase accuracy typically").

**Onemli sonuc:** Kilitliyken TINT icin sabit kucuk bir deger dondurmek
YANLIS DEGIL. Cunku gercekte de dongu onu sabit tutuyor. Simulatorun
mevcut davranisi bu durumda dogru.

### Holdover (acik dongu)

    GNSS 1PPS ──✗  (referansa uyulmuyor)
                        DUZELTME YOK
    Rb 1PPS ────► serbest kosuyor ──► HATA BIRIKIYOR

**Simulatorun mevcut hatasi tam burada:** holdover'da sabit 850 ns
donduruyor, sanki hata birikmiyormus gibi. Duzeltecegimiz sey bu.

---

## 2. Holdover Hata Birikimi Modeli (FAZ 1)

### Turetme

Tek bir fiziksel gercege dayanir: **faz, frekansin integralidir.**

Osilatorun bagil frekans hatasi `y` olsun (birimsiz).
`y = 1e-12` demek "her saniyede 1 pikosaniye kayiyorum" demektir.
Biriken zaman hatasi:

    x(t) = ∫ y dt

**1. katman — sabit frekans hatasi.**
GNSS kaybolduğu anda osilator zaten tam dogru degildi, kucuk bir `y0`
hatasi vardi. Bu sabit kalirsa:

    x(t) = y0 · t          (duz cizgi, DOGRUSAL buyume)

`y0`'i nereden aliyoruz? Uydurmuyoruz. Kilavuzda **FEE (Frequency Error
Estimate)** diye bir sorgu var (§3.6.10) ve tanimi aynen budur:
"Frequency Error Estimate, similar to the Allan Variance using a 1000s
measurement interval". Yani `y0 = FEE`.

**2. katman — frekansin kendisi de kayiyor (yaslanma).**
Rubidyum hucresi zamanla yaslanir; `y` sabit kalmaz, `D` hiziyla degisir:

    y(t) = y0 + D·t    =>    x(t) = y0·t + (D/2)·t²

`D`'yi nereden aliyoruz? §2.9: kilitliyken ADEV **8E-14/gun**'e yaklasiyor.

### Nihai formul

    x(t) = x0 + y0·t + (D/2)·t²
           ▲     ▲          ▲
           │     │          └─ yaslanma (kuadratik; GUNLER mertebesinde onemli)
           │     └─ kayip anindaki frekans hatasi (dogrusal; SAATLER mertebesinde baskin)
           └─ kayip aninda donmus faz hatasi (~0.2 ns)

### Saglama (model dogru mu?)

`y0 = 1.31E-11` (cihazin gercek FEE degeri), `D = 8E-14/gun` ile:

| Gecen sure | Dogrusal terim | Kuadratik terim | Toplam |
|---|---|---|---|
| 1 saat     | 47 ns   | ~0.006 ns | ~47 ns |
| 4.5 saat   | 210 ns  | ihmal     | ~210 ns (HEALTH 0x4 esigi) |
| 1 gun      | 1.13 us | ~3.5 ns   | ~1.13 us |

**Yorum:** Kuadratik terim saatler mertebesinde neredeyse gorunmez,
gunler mertebesinde devreye giriyor. Literaturdeki Rb holdover davranisi
da tam boyledir. Model kendi kendini dogruluyor.

### "GPS yoksa TINT'i neye gore olcuyorsun?"

Hakli bir soru, ve kilavuz cevapliyor (§3.6.2): `SYNC:HOLD:INIT` ile
**zorlanmis holdover**'da GNSS anteni halen takili, sinyal halen geliyor;
cihaz sadece *ona uymayi birakiyor*. Zaman-aralik sayaci olcmeye devam
ediyor. Kilavuzun kendi ifadesi: bu, kullanicinin "GPS'e kilitli
degilken Rubidyum osilatorun kaymasini gormesini" saglar.

**Modelledigimiz gozlem tam olarak budur.**

---

## 3. Kilavuzdan Alinan Gercek Degerler

Modelde kullandigimiz her sayinin kaynagi. Hicbiri uydurma degildir.

### Zaman / faz
| Deger | Kaynak |
|---|---|
| TINT cozunurlugu 1E-10 s (0.1 ns) | §3.6.6 |
| Kilitliyken Rb -> 1PPS faz dogrulugu < 0.2 ns | §1.1 |
| Kilitliyken Filtre OCXO -> Rb < 0.3 ns | §1.1 |
| Kilitliyken ADEV 8E-14/gun'e yaklasiyor | §2.9 |
| FEE ≈ 1000 s Allan varyansi; < 1E-12 gurultu tabaninin alti | §3.6.10 |
| TINT esigi [50, 2000] ns, varsayilan 220 ns -> jam-sync | §3.6.19 |
| Zaman-aralik sayaci cozunurlugu 20 ps | §1.1 |

### ADEV tablosu (Premium secenek, GPS kilitli, Sekil 2.19)
| tau | sigma(tau) |
|---|---|
| 1 s | 1.76E-12 |
| 10 s | 4.15E-12 |
| 100 s | 6.11E-12 |
| 1000 s | 4.74E-12 |
| 4000 s | 1.47E-12 |

### SYNC:HEALTH? bit haritasi (§3.6.18 — tam liste)
| Bit | Kosul |
|---|---|
| 0x4    | referansa faz farki > 210 ns |
| 0x8    | calisma suresi < 200 saniye |
| 0x10   | holdover > 60 saniye |
| 0x20   | FEE sinir disi |
| 0x100  | kisa donem drift (ADEV@100s) > 100 ns |
| 0x200  | faz-reset sonrasi ilk 3 dakika |
| 0x400  | Rubidyum osilator alarmi |
| 0x800  | guclu jamming (>=50, aralik 0-255) ve GNSS fix yok |
| 0x1000 | filtre osilator dongusu kilitli degil |

0x0 = tamamen saglikli, isinmis, kilitli cihaz.

### SERVo:STATe? durum makinesi (§3.10.3)
| Deger | Anlam |
|---|---|
| 0 | Rubidyum/filtre osilator isinmasi |
| 1 | Holdover |
| 2 | Kilitleniyor (Rubidyum/filtre egitimi) |
| 4 | (tanimsiz) |
| 5 | **Holdover ama halen faz kilitli** — GNSS kaybindan sonra ~100 s bu durumda kalir |
| 6 | Kilitli, GNSS aktif |

**Not:** Bu durum makinesi simulatorde HENUZ YOK. FAZ 3'te eklenecek.
Ozellikle durum 5 (gecis durumu) gercekci bir ayrinti.

### Isinma
| Deger | Kaynak |
|---|---|
| Atomik kilide < 2 dakika | §1.1 |
| LOCK_OK tipik olarak < 20 dakika | §2.5 |
| Fazlarin ns seviyesinde tam oturmasi 24 saate kadar | §2.9, Sekil 2.20 |
| Guc: isinmada ~18 W, birkac dakika sonra < 5.6 W | §2.2 |
| CSAC secenegi: < 1.4 W kalici | §2.2 |

### Diger
| Deger | Kaynak |
|---|---|
| Seri: 115200 baud, 8N1, akis kontrolu yok | §2.2 |
| Sicaklik araligi -40 .. +70 C | §1.1 |
| EFC Relative: -100% .. +100% | §3.7.1 |
| EFC Absolute: parts-per-trillion (1E-12) cinsinden | §3.7.2 |
| DIAG:LIFetime:COUNt? saat cinsinden | §3.7.5 |
| Jamming seviyesi araligi 0-255 | §3.6.18 |

---

## 4. Kararlar

### K-1: Fizik modeli ayri bir modulde, saf fonksiyon olarak
- **Durum**: Holdover formulunu nereye koyacagiz?
- **Karar**: `src/gnsdo_simulator/models/holdover.py` icinde, hicbir I/O
  veya global durum kullanmayan saf fonksiyonlar olarak.
- **Neden**: Saf fonksiyon = ayni girdi hep ayni cikti. Testte gercek
  zaman beklemeye gerek kalmaz; "4.5 saat gecmis olsaydi" degerini
  dogrudan parametre olarak veririz. Ayrica formulu komut isleme
  mantigindan ayirmak, bildiriyi yazarken modeli tek basina anlatmayi
  kolaylastirir.
- **Alternatif**: Formulu dogrudan `commands/sync.py` icine gomek.
  Reddedildi: test edilmesi zor, ve komut katmani "cihaz fizigi" bilmek
  zorunda kalirdi (katmanli mimariyi bozar).

### K-2: Zaman hizlandirma (time-scale) EKLENMEYECEK
- **Durum**: 210 ns esigine ulasmak gercek zamanda 4.5 saat suruyor.
  Demo/test icin yavas.
- **Karar**: Simulator GERCEK ZAMANDA calissin. Hizlandirma bayragi yok.
  Testler modeli dogrudan cagirip sahte gecmis sure verir.
- **Neden**: Simulatorun amaci gercek cihaz gibi davranmak. Ona baglanan
  test uygulamasi "bu cihaz nicin 100 kat hizli kaiyor?" dememeli.
  Hizlandirma ihtiyaci aslinda bir TEST ihtiyaci, o yuzden test
  katmaninda cozulmeli.
- **Alternatif**: `--time-scale 100` bayragi. Reddedildi: cihazin
  gozlemlenebilir davranisini gercek disi yapar. Ileride demo icin
  gercekten gerekirse tekrar tartisilir.

### K-3: y0 degeri FEE'den okunacak, ayri bir sabit tanimlanmayacak
- **Durum**: Holdover drift hizi icin yeni bir parametre mi tanimlayalim?
- **Karar**: Hayir. `state.freq_error_estimate` (zaten var, SYNC? ciktisinda
  gorunuyor) dogrudan `y0` olarak kullanilacak.
- **Neden**: Kilavuzda FEE'nin tanimi zaten "frekans hata tahmini"
  (§3.6.10). Ayni fiziksel buyuklugu iki farkli alanda tutmak, ikisinin
  birbiriyle celismesine yol acar. Tek kaynak ilkesi.
- **Yan fayda**: `SYNC:FEE?` ile `SYNC:TINT?` artik birbiriyle tutarli
  olur — kullanici FEE'yi okuyup TINT'in ne hizla buyuyecegini kendisi
  hesaplayabilir. Gercek cihazda da boyledir.

### K-4: Kilitliyken TINT sabit kalmaya devam edecek
- **Durum**: "Her seyi dinamik yapalim" durtusu.
- **Karar**: Kilitliyken TINT sabit kucuk deger olarak kalacak (FAZ 2'de
  uzerine gurultu eklenecek, ama trend eklenmeyecek).
- **Neden**: Kapali dongu zaten TINT'i sifira cekiyor (§1.1: < 0.2 ns).
  Kilitliyken TINT'e trend eklemek FIZIKSEL OLARAK YANLIS olurdu —
  dongunun calismadigi anlamina gelirdi.
- **Ders**: "Dinamik" demek "her sey degissin" demek degil. Neyin
  degismesi GEREKTIGINI fizik soyler.

### K-5: Holdover'da faz hatasi giriste dondurulacak (x0)
- **Durum**: Holdover baslarken TINT sifirdan mi baslasin?
- **Karar**: Hayir. Holdover'a girildigi andaki TINT degeri `x0` olarak
  saklanacak, birikim onun uzerine eklenecek.
- **Neden**: Fiziksel olarak faz sureklidir — GNSS kesildigi anda faz
  farki sifira atlamaz, neyse o kalir ve oradan itibaren buyumeye baslar.

---

## 5. Duzeltilen Gerceklik Hatalari

Modeli kurarken fark edilen, mevcut kodda GERCEK CIHAZLA CELISEN noktalar:

### D-1: SYNC:HOLD:DUR? holdover disinda "0,0" donuyordu
- **Gercek davranis** (§3.6.1): "If the Receiver is not in holdover, the
  response quantifies the PREVIOUS holdover." Yani bir onceki holdover'in
  suresini dondurmeli.
- **Duzeltme**: `last_holdover_duration_s` alani eklendi; holdover
  bitince oraya yazilip sonraki sorgularda dondurulecek.

### D-2: HEALTH 0x4 kontrolu isaretli karsilastirma yapiyordu
- **Sorun**: `_tint_seconds(state) > 210e-9` — TINT negatif olabilir
  (osilator geride kalirsa). Negatif tarafta 210 ns'yi asan bir hata
  YAKALANMAZDI.
- **Gercek davranis** (§3.6.18): "If the phase offset to reference is
  >210ns" — offset bir BUYUKLUK, isaretten bagimsiz.
- **Duzeltme**: `abs()` kullanilacak.

---
  
## 6. Yol Haritasi

| Faz | Icerik | Durum |
|---|---|---|
| 1 | Holdover hata birikimi (bu belge) | devam ediyor |
| 2 | Olcumlere deterministik gurultu (sicaklik, voltaj, TINT jitter) | planli |
| 3 | Isinma rampasi + SERVo:STATe durum makinesi (0->2->6, ve 5) | planli |
| 4 | Bildiri | planli |

**FAZ 2 notu**: Gurultu DETERMINISTIK olacak (sabit tohumlu rastgele
uretec). Neden: ayni senaryoyu iki kez calistirinca ayni sonucu almak,
hem test edilebilirlik hem de hata ayiklama icin sart.
