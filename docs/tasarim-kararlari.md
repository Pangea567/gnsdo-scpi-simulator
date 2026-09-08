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

### K-6: Gurultu ZAMANIN FONKSIYONU, rastgele sayi akisi degil
- **Durum**: Olcumlere gurultu eklerken akla ilk gelen "her sorguda
  random.gauss() cagir" yaklasimi.
- **Karar**: Reddedildi. Gurultu `deger(t) = taban + genlik*f(t)`
  seklinde, PROGRAM BASLANGICINDAN beri gecen surenin fonksiyonu.
- **Neden**: Iki ayri sebep:
  1. **Fiziksel**: Cihazin sicakligi BELLI BIR ANDA belli bir
     degerdir. Ayni saniye icinde iki kez sorarsan ayni cevabi
     almalisin. Rastgele akista deger, KAC KEZ SORDUGUNA bagli olur
     -- sanki sen sordukca cihazin sicakligi degisiyormus gibi.
  2. **Pratik**: Tekrarlanabilirlik. Bir hata gordugunde ayni kosulu
     yeniden uretemezsen hata ayiklayamazsin.
- **Nasil**: Oranlari altin oranla IRRASYONEL yapilmis birkac sinusun
  toplami. Tam sayi oranlari kullansaydik desen kisa surede tekrarlar
  ve gozle fark edilen yapay bir periyodiklik olusurdu.
- **Alt karar -- duvar saati degil, gecen sure**: Duvar saati
  kullansaydik ayni senaryo iki farkli gunde farkli degerler uretirdi.

### K-7: Tohumdan faz uretirken Python'un hash() fonksiyonu KULLANILMIYOR
- **Durum**: Her olcum alani farkli bir desen kullanmali (yoksa
  sicaklik, voltaj ve akim ayni anda ayni yone gider, yapay gorunur).
  Bunun icin alan adindan bir faz kaymasi uretiyoruz.
- **Karar**: `hash("temperature")` yerine kendi sabit hesabimiz.
- **Neden**: Python, METINLER icin hash()'i her calistirmada RASTGELE
  tohumlar (guvenlik onlemi). hash() kullansaydik determinizm
  SESSIZCE kaybolurdu -- kod dogru gorunur, testler tek calistirmada
  gecer, ama iki farkli calistirma farkli sonuc verirdi.
- **Dogrulama**: Testler farkli `PYTHONHASHSEED` degerleriyle
  calistirilarak dogrulandi.

### K-8: Gurultu VARSAYILAN OLARAK ACIK
- **Karar**: `noise.enabled: true` varsayilan; kapatmak istisna.
- **Neden**: Gercek cihaz davranisi budur. Gurultusuz mod bir
  "ozellik" degil, bir TEST/KARSILASTIRMA araci.
- **Nasil kapatilir**: `enabled: false` ya da `scale: 0.0`. Ara
  degerler (`scale: 0.5`) genligi olceklendirir.

### K-9: CSAC sicakligindaki 47 -> 54 tirmanisi FAZ 2'ye AIT DEGIL
- **Durum**: Gercek cihaz ciktilarinda CSAC sicakligi 47 ile 54
  arasinda gorulmustu. Ilk plan bunu +/- 3.5'luk bir gurultu genligi
  olarak modellemekti.
- **Karar**: Yanlis. Bu bir SALINIM degil, TEK YONLU TIRMANIS --
  cihaz acildiktan sonra 54 civarina cikar ve ORADA KALIR.
- **Neden**: Cihazi calistiran kisinin gozlemi. Genis araligi gurultu
  sanip +/- 3.5 genlik verseydik, cihaz 47 ile 54 arasinda surekli
  gidip gelirdi -- gercekte olmayan bir davranis.
- **Sonuc**: FAZ 2'de taban 54, genlik +/- 0.25 (kisa vadeli jitter).
  Tirmanisin kendisi FAZ 3'e (isinma rampasi) birakildi.
- **Ders**: Gozlenen bir ARALIK, otomatik olarak gurultu genligi
  demek degildir. Once "bu aralik bir salinim mi, yoksa bir gecis mi?"
  diye sormak gerekir.

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
  
## 5.7 Gercek Cihaz Kayitlariyla Hizalama Turu

Kaynak: `Rubidium GNSDO SCPI Device.docx` -- gercek cihazdan alinmis
komut girdi/cikti kayitlari. Bu belge KILAVUZDA OLMAYAN seyleri
gosterdi ve modelimizdeki bir kisim hatayi ortaya cikardi.

**Genel ders:** Kilavuz ne YAPILMASI gerektigini anlatir; kayitlar
cihazin GERCEKTE ne yaptigini gosterir. Ikisi her zaman ortusmuyor.

### D-4: Kilitli TINT modeli yanlisti (EN ONEMLI)
- **Bizim modelimiz**: taban +12 ns sabit, jitter +/-0.2 ns. Yani
  hicbir zaman negatif olmuyor, neredeyse hic oynamiyordu.
- **Gercek kayitlar**:
  `1.133E-08  -7.873E-09  -1.179E-08  9.063E-09  2.672E-09  6.763E-08`
  TINT SIFIRIN ETRAFINDA, arti ve eksi yonde, ~+/-12 ns salaniyor.
- **Hatanin kaynagi**: Kilavuz §1.1'deki "better than 0.2ns AVERAGE
  phase accuracy" ifadesini "jitter genligi 0.2 ns" diye okuduk.
  "average" kelimesi kilit: ORTALAMA sifira 0.2 ns yakin demek;
  anlik okuma cok daha genis salinir.
- **Duzeltme**: taban 0.0, jitter genligi 12 ns.
- **Yan etki**: D-2'deki `abs()` duzeltmesi artik cok daha kritik --
  TINT gercekten negatife geciyor.
- **Ders**: Bir spesifikasyon sayisini okurken yanindaki niteleyiciye
  (average, typical, peak, RMS) dikkat et. Ayni sayi, niteleyiciye
  gore tamamen farkli bir sey anlatir.

### D-5: MEAS:CURR? akim dondurmuyor
- **Bizim cevabimiz**: `0.42` (akim, amper sanmisiz).
- **Gercek kayit**: `51.3210` -- yanindaki `MEAS:TEMP?` ise `51.1479`.
- **Kilavuz §3.8.3**: "Legacy SCPI command, instead of OCXO current
  this command displays either the internal Rubidium temperature or
  PCB temperature."
- **Ders**: Eski cihazlarda komut ADI ile ISI arasindaki uyumsuzluk
  siktir -- ad geriye donuk uyumluluk icin korunur, islev degisir.

### D-6: CSAC ve PCB sicakligi bagimsiz degil
Gercek kayitlardaki dort MEAS? cifti:

| PCB | CSAC | fark |
|---|---|---|
| 46.5688 | 47.83 | +1.261 |
| 52.7762 | 54.10 | +1.324 |
| 52.8652 | 54.17 | +1.305 |
| 49.7419 | 51.13 | +1.388 |

Ortalama fark **+1.32 C**, dordunde de tutuyor. Fiziksel aciklama:
CSAC modulu isi KAYNAGIDIR, cevresindeki kart ondan serindir.

CSAC sicakligi artik PCB'den turetiliyor. Bagimsiz modelleseydik ters
yonlere gidip gercekte hic gorulmeyen kombinasyonlar uretebilirlerdi.

### D-7: EFControl Absolute ve Relative de bagimsiz degil
Gercek kayitlar: `-82 -> -0.410000%`, `-88 -> -0.440000%`,
`-128 -> -0.640000%`, `-21 -> -0.105000%`. Hepsinde
**Absolute = Relative x 200**.

Bagintinin YONU de veriden okundu: Absolute her zaman TAM SAYI,
Relative ise 6 ondalikta TAM cikiyor. Rastgele bir yuzde olsaydi bu
mumkun olmazdi -- demek ki asil deger tam sayi olan Absolute
(muhtemelen bir DAC adimi), yuzde ondan hesaplaniyor.

- **Ders**: Verideki sayilarin BICIMI, aralarindaki nedenselligi ele
  verir. "Hangisi hangisinden turuyor?" sorusunu, tam sayi olani
  bularak cevaplayabildik.

### D-8: Bilinmeyen komutta cihaz sessiz kalmiyor
- **Bizim davranisimiz**: hicbir sey yazmiyorduk.
- **Gercek cihaz**: `Command Error` donduruyor.
- **Nicin onemli**: Sessizlik istemci acisindan belirsizdir -- komut
  mu taninmadi, baglanti mi koptu, ayirt edilemez.
- **Tasarim notu**: Parser hala `None` donduruyor ("bilmiyorum"
  demenin dogru yolu); bunu gorunur mesaja cevirmek SerialServer'in
  isi. Boylece parser protokol metinlerinden habersiz kaliyor.

### D-9: Sayi bicimleri sabit ondalikli olmali
Gercek cihaz `CSAC Temperature: 54.10` yaziyor -- sondaki sifir
DURUYOR. PCB sicakligi 4 ondalik (`46.5688`), CSAC 2 ondalik. Biz
`str()` kullaniyorduk, `54.1` yaziyordu. Sabit genislikte alan
bekleyen bir istemci icin bu fark ayristirma hatasina yol acabilir.

### K-10: Gercek cihazin TUTARSIZLIGINI taklit etmiyoruz
- **Durum**: Kayitlarda `GPS:SAT:TRAC:COUN?` -> 20 iken
  `GPS:SAT:VIS:COUN?` -> 19. Takip edilen, gorunurden fazla.
- **Muhtemel aciklama**: Iki sayac farkli seyleri sayiyor.
  `SYST:STAT?` ciktisindaki "Tracking:14 + Not Tracking:6 = 20" ile
  TRAC:COUN?'un 20'si ortusuyor -- o, alicinin kanal tablosunun
  TAMAMINI sayiyor olabilir. Ayrica ikisi farkli anlarda ornekleniyor.
  (Bu bir yorum; kilavuz acikca yazmiyor.)
- **Karar**: Taklit ETMIYORUZ. Config tutarsizsa uyari loglanip
  tracking, visible'a kisitlaniyor.
- **Neden**: Simulatorun tutarli olmasi, gercek cihazin bir olcum
  artifaktini yeniden uretmesinden daha degerli. Bir test uygulamasi
  gelistiren kisi "takip > gorunur" gorurse kendi kodunda hata arar.

### Kalan Bilinen Farklar (henuz ele alinmadi)
- **FEE sabit tutuluyor**: gercek kayitlarda `1.31E-11`, `2.49E-11`,
  `1.59E-11` diye degisiyor. Holdover birikim HIZINI belirleyen
  parametre oldugu icin ayrica ele alinmali.
- **PCB sicaklik araligi**: kayitlarda 46.57 - 52.87. Dusuk okumalar
  muhtemelen isinma sirasinda alindi; kararli durum ust kumede
  (~52.8). Tirmanis FAZ 3'e ait.

---


## 5.8 FAZ 3 -- Isinma Rampasi ve Servo Durum Makinesi

### K-11: Isil rampa USTEL, dogrusal degil
- **Karar**: `T(t) = T_son - (T_son - T_bas) * e^(-t/tau)`
- **Neden**: Isi kaybi, cisimle ortam arasindaki SICAKLIK FARKI ile
  orantilidir (Newton soguma yasasi). Fark buyukken hizli isinir,
  fark kapandikca yavaslar. Dogrusal bir rampa fiziksel olarak yanlis
  olurdu: sicaklik hedefe varinca aniden durmaz, ona asimptotik
  yaklasir -- ve dogrusal model devam etseydi hedefi ASARDI.
- **tau = 600 s**: Kilavuz §2.5'teki 20 dakikalik kilit suresiyle
  uyumlu bir isil oturma profili verir (30 dk'da farkin %95'i kapanir).
- **DOGRULAMA**: Bu parametrelerle model 15. dakikada PCB 46.60 C /
  CSAC 47.92 C uretiyor. Gercek cihaz kayitlarindaki EN SOGUK MEAS?
  cifti 46.5688 / 47.83 idi. tau'yu kilavuzun kilit suresinden sectik,
  bu sayilara BAKARAK degil -- model bagimsiz bir gozlemi yeniden
  uretiyor.

### K-12: Ortam sicakligi bir VARSAYIMDIR
- **Durum**: Rampanin baslangic noktasi (T_bas) icin bir degere
  ihtiyac var, ama kilavuz ortam sicakligi vermiyor ve gercek cihaz
  kayitlari da acilis anini icermiyor.
- **Karar**: 25 C (ic mekan oda sicakligi), config'ten ayarlanabilir.
- **Neden**: Kilavuz §1.3.4 cihazin ic mekan kullanimi icin
  tasarlandigini soyluyor. Deger yanlissa tek satirla duzelir.
- **Ders**: Elde veri olmayan bir parametreyi UYDURMAK ile
  VARSAYIM OLARAK ISARETLEMEK ayni sey degil. Ikincisi, sonradan
  duzeltilebilir olmasini saglar.

### D-10: SYNC:LOCKED? yanlis esigi kullaniyordu
- **Bizim davranisimiz**: Isinma senaryosunda 120 saniye sonra
  "kilitli" donuyorduk.
- **Sorun**: 120 saniye kilavuz §1.1'deki ATOMIK kilit suresidir
  ("less than 2 minutes warmup time to atomic lock"). Ama
  SYNC:LOCKED?, §3.6.11'e gore atomik kilidi degil "Rubidyum
  osilatoru kontrol eden PLL"in durumunu, yani GNSS'E KILITLENMEYI
  bildirir. O ise §2.5'e gore tipik olarak 20 DAKIKA surer.
- **Duzeltme**: Kilit karari artik servo durum makinesinden geliyor;
  yalnizca durum 6 gercek kilittir.
- **Ders**: Iki farkli "kilit" kavramini ayni sanmisiz. Kilavuzda
  ayni kelimenin farkli alt sistemlerde farkli anlamlari olabiliyor;
  hangi komutun HANGI kilidi bildirdigini tek tek dogrulamak gerek.

### K-13: SERVo alt sistemi eklendi (gorev taniminda yoktu)
- **Durum**: Gorev tanimindaki komut listesinde SERVo yok. Ama hem
  kilavuzda (§3.10) hem gercek cihaz kayitlarinda var.
- **Karar**: `SERVo:STATe?` ve `SERV?` eklendi.
- **Neden**: Cihaz aciliskan kilide TEK ADIMDA gecmez:
  `0 isinma -> 2 kilitleniyor -> 6 kilitli`. SYNC:LOCKED? ilk ikisinde
  de "0" doner, yani ikisini AYIRT EDEMEZ. Bir izleme yazilimi
  "neden hala kilitlenmedi?" sorusuna ancak SERVo:STATe? ile cevap
  verebilir: cihaz henuz mi isiniyor, yoksa isindi da GNSS'e mi
  kilitlenemiyor?
- **Not**: Deger SAKLANMIYOR, HESAPLANIYOR. SYNC:LOCKED? ile ayni
  kaynaktan okuduklari icin celisemezler.

### K-14: Gercek ciktidaki bicim tutarsizliklari KORUNUYOR
- **Durum**: Gercek `SERV?` ciktisinda etiket bicimi tutarsiz:
  `LOOP:` bitisik, `EFC SCALE :` ayrik, `FASTLOCK PERIOD  :` iki
  bosluklu.
- **Karar**: Aynen taklit ediliyor, "duzeltilmiyor".
- **Neden**: Ciktiyi sabit bicimde ayristiran bir istemci, bizim
  duzelttigimiz bir bosluk yuzunden gercek cihazda calisip
  simulatorde calismayabilir. Simulatorun amaci gercegi taklit
  etmek, guzellestirmek degil.
- **Not**: Bu, K-10 (tutarsizligi taklit etmeme karari) ile CELISMEZ.
  Oradaki tutarsizlik cihazin bir OLCUM artifaktiydi ve kullaniciyi
  yaniltirdi; buradaki ise PROTOKOL bicimidir ve istemci ona bagimli
  olabilir.

### Isinma profili (olculen)

| Dakika | PCB | CSAC | SERVo:STATe? | SYNC:LOCKED? |
|---|---|---|---|---|
| 0  | 25.00 | 26.32 | 0 | 0 |
| 1  | 27.65 | 28.97 | 0 | 0 |
| 2  | 30.04 | 31.36 | 2 | 0 |
| 5  | 35.94 | 37.26 | 2 | 0 |
| 10 | 42.57 | 43.89 | 2 | 0 |
| 15 | 46.60 | 47.92 | 2 | 0 |
| 20 | 49.04 | 50.36 | 6 | 1 |
| 30 | 51.42 | 52.74 | 6 | 1 |
| 60 | 52.73 | 54.05 | 6 | 1 |

---


## 6. Yol Haritasi

| Faz | Icerik | Durum |
|---|---|---|
| 1 | Holdover hata birikimi (bu belge) | **TAMAMLANDI** |
| 2 | Olcumlere deterministik gurultu (sicaklik, voltaj, TINT jitter) | **TAMAMLANDI** |
| 3 | Isinma rampasi + SERVo:STATe durum makinesi (0->2->6, ve 5). CSAC sicakliginin 47->54 tirmanisi da burada (bkz. K-9) | **TAMAMLANDI** |
| 4 | Bildiri | planli |

**FAZ 2 notu**: Gurultu DETERMINISTIK olacak (sabit tohumlu rastgele
uretec). Neden: ayni senaryoyu iki kez calistirinca ayni sonucu almak,
hem test edilebilirlik hem de hata ayiklama icin sart.
