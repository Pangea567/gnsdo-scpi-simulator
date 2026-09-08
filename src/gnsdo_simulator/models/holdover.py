"""
models/holdover.py

HOLDOVER HATA BIRIKIMI MODELI.

PROBLEM:
  Cihaz GPS'e kilitliyken, kapali bir kontrol dongusu TINT'i (Rubidyum
  1PPS'i ile GNSS 1PPS'i arasindaki zaman farkini) surekli sifira
  ceker. GPS kesilince bu dongu ACILIR: artik duzeltme yoktur ve
  osilatorun kucuk frekans hatasi zamanla ZAMAN hatasina donusur,
  yani hata BIRIKIR. Kilavuzun kendi kelimesiyle cihaz "coasting"
  (kendi basina yurume) moduna girer (§3.6.1).

TURETME:
  Tek bir fiziksel gercege dayanir: FAZ, FREKANSIN INTEGRALIDIR.

  Osilatorun bagil frekans hatasi y olsun (birimsiz buyukluk).
  y = 1e-12 demek "her gecen saniyede 1 pikosaniye kayiyorum" demektir.
  Biriken zaman hatasi:

      x(t) = integral( y dt )

  1. katman -- SABIT frekans hatasi:
     GPS kaybolduğu anda osilator zaten tam dogru degildi, kucuk bir
     y0 hatasi vardi. Bu sabit kalirsa hata DOGRUSAL buyur:

         x(t) = y0 * t

     y0'i UYDURMUYORUZ: kilavuzdaki FEE (Frequency Error Estimate,
     §3.6.10) sorgusunun tanimi tam olarak budur -- "frekans hata
     tahmini". Yani y0 = FEE.

  2. katman -- frekansin KENDISI de kayiyor (yaslanma):
     Rubidyum hucresi zamanla yaslanir, y sabit kalmaz:

         y(t) = y0 + D*t    =>    x(t) = y0*t + (D/2)*t^2

     D'yi de uydurmuyoruz: §2.9'a gore kilitliyken ADEV 8E-14/GUN'e
     yaklasiyor -- bu, osilatorun gunluk drift mertebesidir.

NIHAI FORMUL:

      x(t) = x0 + y0*t + (D/2)*t^2
             ^    ^          ^
             |    |          +-- yaslanma (kuadratik; GUNLER mertebesinde onemli)
             |    +------------- kayip anindaki frekans hatasi
             |                   (dogrusal; SAATLER mertebesinde baskin)
             +------------------ kayip aninda DONMUS faz hatasi

  x0 nicin var? Cunku faz SUREKLIDIR: GPS kesildigi anda faz farki
  sifira atlamaz, o an neyse o kalir ve buyumeye ORADAN baslar.

SAGLAMA (y0 = 1.31E-11, D = 8E-14/gun ile):
      1 saat   ->  ~47 ns      (kuadratik terim ~0.006 ns, gorunmez)
      4.5 saat -> ~210 ns      (SYNC:HEALTH? 0x4 esigi)
      1 gun    -> ~1.13 us     (kuadratik terim ~3.5 ns)

  Yorum: kuadratik terim saatler mertebesinde neredeyse yok, gunler
  mertebesinde devreye giriyor. Literaturdeki Rb holdover davranisi
  da boyledir -- model kendi kendini dogruluyor.

"GPS YOKSA TINT'I NEYE GORE OLCUYORSUN?"
  Hakli bir soru; kilavuz cevapliyor (§3.6.2): SYNC:HOLD:INIT ile
  ZORLANMIS holdover'da GNSS anteni halen takilidir, sinyal halen
  gelir; cihaz sadece ONA UYMAYI birakir. Zaman-aralik sayaci olcmeye
  devam eder. Kilavuzun ifadesiyle bu, kullanicinin "GPS'e kilitli
  degilken Rubidyum osilatorun kaymasini gormesini" saglar.
  Modelledigimiz gozlem tam olarak budur.

BU MODULUN KURALI:
  Buradaki fonksiyonlar SAFTIR -- datetime.now() cagirmaz, DeviceState
  okumaz, hicbir sey yazmaz. Gecen sureyi PARAMETRE olarak alirlar.
  Boylece "4.5 saat gecmis olsaydi ne olurdu?" sorusunu testte gercek
  zamanda beklemeden sorabiliriz.
"""

SECONDS_PER_DAY = 86400.0

# Kilavuz §2.9: kilitliyken ADEV "8E-014 per day"e yaklasiyor.
# Bu degeri Rubidyum osilatorun gunluk yaslanma/drift hizi (D) olarak
# kullaniyoruz -- yani "bagil frekans hatasi her GUN ne kadar degisiyor".
RB_DRIFT_PER_DAY = 8e-14

# Kilavuz §1.1: kilitliyken Rubidyum 1PPS'in referansa faz dogrulugu
# "better than 0.2ns average". Holdover'a girerken donan x0 icin
# makul varsayilan baslangic degeri budur.
NOMINAL_LOCKED_TINT_SECONDS = 0.2e-9


def drift_per_second(drift_per_day: float = RB_DRIFT_PER_DAY) -> float:
    """
    Gun basina drift'i saniye basina cevirir.

    Nicin ayri bir fonksiyon? Formulde D'nin birimi 1/saniye olmali
    ama kilavuz degeri GUN cinsinden veriyor. Bu donusumu tek bir
    yerde yaparak, birim karisikligindan (fizik kodundaki en yaygin
    hata kaynagi) kacaniyoruz.
    """
    return drift_per_day / SECONDS_PER_DAY


def holdover_tint_seconds(
    elapsed_seconds: float,
    entry_tint_seconds: float = NOMINAL_LOCKED_TINT_SECONDS,
    freq_error_estimate: float = 0.0,
    drift_per_day: float = RB_DRIFT_PER_DAY,
) -> float:
    """
    Holdover'a girildikten elapsed_seconds saniye sonra biriken TINT
    degerini (SANIYE cinsinden) hesaplar.

        x(t) = x0 + y0*t + (D/2)*t^2

    Parametreler:
        elapsed_seconds     -- holdover'a girildiginden beri gecen sure (t)
        entry_tint_seconds  -- holdover'a girildigi andaki TINT (x0)
        freq_error_estimate -- kayip anindaki bagil frekans hatasi (y0),
                               cihazin FEE degeri
        drift_per_day       -- osilator yaslanma hizi (gun basina, D)

    Isaret korunur: y0 negatifse osilator geri kalir ve TINT negatif
    yonde buyur. Gercek cihazda da TINT isaretli bir buyukluktur
    (osilator referansin onunde mi arkasinda mi).

    Gecmise dogru (negatif sure) hesap anlamsiz oldugu icin, t<=0
    durumunda giris degeri aynen dondurulur.
    """
    if elapsed_seconds <= 0:
        return entry_tint_seconds

    linear_term = freq_error_estimate * elapsed_seconds
    quadratic_term = 0.5 * drift_per_second(drift_per_day) * elapsed_seconds**2

    return entry_tint_seconds + linear_term + quadratic_term
