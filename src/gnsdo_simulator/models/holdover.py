"""
models/holdover.py

HOLDOVER HATA BIRIKIMI MODELI.

PROBLEM:
  Cihaz GNSS'e kilitliyken, kapali bir kontrol dongusu TINT'i (Rubidyum
  1PPS'i ile GNSS 1PPS'i arasindaki zaman farkini) surekli sifira ceker.
  GNSS kesilince bu dongu ACILIR: artik duzeltme yoktur ve osilatorun
  kucuk frekans hatasi zamanla ZAMAN hatasina donusur, yani hata BIRIKIR.
  Kilavuzun kendi kelimesiyle cihaz "coasting" moduna girer (§3.6.1).

TURETME:
  Tek bir fiziksel gercege dayanir: FAZ, FREKANSIN INTEGRALIDIR.

  Osilatorun bagil frekans hatasi y olsun (boyutsuz). y = 1e-12 demek
  "her gecen saniyede 1 pikosaniye kayiyorum" demektir. Biriken zaman
  hatasi x(t) = integral(y dt). y holdover boyunca sabit kabul edilirse:

      x(t) = x0 + y_h * t          (x ve t saniye, y_h boyutsuz)
             ^    ^
             |    +-- holdover boyunca gecerli, ISARETLI etkin frekans hatasi
             +------- kayip aninda DONMUS faz hatasi

  x0 nicin var? Cunku faz SUREKLIDIR: GNSS kesildigi anda faz farki
  sifira atlamaz, o an neyse o kalir ve buyumeye ORADAN baslar.

  y_h NEREDEN GELIR? Burasi dikkat isteyen yer. Kilavuz §3.6.10'daki FEE
  (Frequency Error Estimate) degerini dogrudan y_h sanmak CAZIP ama
  dogru degil: kilavuz FEE'yi 1000 s ortalama suresinde Allan varyansina
  BENZER bir buyukluk olarak tanimliyor, yani isaretli bir frekans
  sapmasi olarak degil. Bu yuzden:
    - y_h'nin BUYUKLUGU kaydedilmis FEE degerlerinden olceklenir
      (1.3-2.5e-11 araligi), ama
    - isaret ve olcekleme ACIK bir model parametresidir
      (`sync.holdover_frequency_error`).
  Yani varsayimi modele gommek yerine gorunur kiliyoruz.

MODEL DOGRUSALDIR -- YASLANMA TERIMI YOK:
  Onceki surumde ikinci dereceden bir yaslanma terimi vardi:
  x(t) = x0 + y0*t + (D/2)*t^2, ve D kilavuz §2.9'daki 8E-14 degerinden
  alinmisti. BU YANLISTI. §2.9'daki 8E-14 bir ALLAN SAPMASI (ADEV)
  rakamidir: belirli bir ortalama suresinde kararlilik olcusu, boyutsuz.
  Yaslanma katsayisi ise dy/dt'dir, birimi 1/gun. Ikisi ayni sey degil,
  birimleri bile uyusmuyor. Terim ve `RB_DRIFT_PER_DAY` sabiti
  kaldirildi; `sync.drift_per_day` ayari artik sessizce yok sayilmiyor,
  hata veriyor.

  Sayisal olarak eski terim kucuktu (1 gunde ~%0.2) -- yani sorun
  sonuclarda degil, ATIFTA idi: kaynagin desteklemedigi bir fiziksel
  yorum modele gomulmustu.

"GNSS YOKSA TINT'I NEYE GORE OLCUYORSUN?"
  Hakli bir soru; kilavuz cevapliyor (§3.6.2): SYNC:HOLD:INIT ile
  ZORLANMIS holdover'da GNSS anteni halen takilidir, sinyal halen gelir;
  cihaz sadece ONA UYMAYI birakir. Zaman-aralik sayaci olcmeye devam
  eder. Kilavuzun ifadesiyle bu, kullanicinin "GNSS'e kilitli degilken
  Rubidyum osilatorun kaymasini gormesini" saglar. Modelledigimiz gozlem
  tam olarak budur.

BU MODULUN KURALI:
  Buradaki fonksiyonlar SAFTIR -- datetime.now() cagirmaz, DeviceState
  okumaz, hicbir sey yazmaz. Gecen sureyi PARAMETRE olarak alirlar.
  Boylece "3.24 saat gecmis olsaydi ne olurdu?" sorusunu testte gercek
  zamanda beklemeden sorabiliriz.

KAPSAM UYARISI:
  Bu model, fiziksel osilatorun metrolojik bir ongorusu DEGILDIR.
  Amaci, istemci yazilimi icin tekrar uretilebilir ve zaman-tutarli bir
  TINT davranisi uretmektir.
"""

SECONDS_PER_DAY = 86400.0

# Kilitliyken TINT'in ORTALAMA degeri. Kapali kontrol dongusu TINT'i
# sifira cektigi icin bu SIFIRDIR; anlik okuma sifirin etrafinda
# salinir. Eskiden sabit +12 ns taban sanilmisti; gercek kayitlar
# bunu duzeltti.
NOMINAL_LOCKED_TINT_SECONDS = 0.0


def holdover_tint_seconds(
    elapsed_seconds: float,
    entry_tint_seconds: float = NOMINAL_LOCKED_TINT_SECONDS,
    freq_error_estimate: float = 0.0,
) -> float:
    """
    Holdover'a girildikten elapsed_seconds saniye sonra biriken TINT
    degerini (SANIYE cinsinden) hesaplar.

        x(t) = x0 + y_h * t

    Parametreler:
        elapsed_seconds     -- holdover'a girildiginden beri gecen sure (t)
        entry_tint_seconds  -- holdover'a girildigi andaki TINT (x0)
        freq_error_estimate -- ISARETLI etkin frekans hatasi (y_h).
                               Tarihsel bir ad; cagiran taraf bu degeri
                               ACIKCA verir. Fonksiyon bu degeri bir
                               Allan istatistiginden TURETMEZ.

    Isaret korunur: y_h negatifse osilator geri kalir ve TINT negatif
    yonde buyur. Gercek cihazda da TINT isaretli bir buyukluktur
    (osilator referansin onunde mi arkasinda mi). Bu yuzden
    SYNC:HEALTH? 0x4 kontrolu mutlak deger kullanmak zorundadir --
    yoksa negatif yonde 210 ns'yi asan bir hata KACIRILIR.

    Gecmise dogru (negatif sure) hesap anlamsiz oldugu icin t<=0
    durumunda giris degeri aynen dondurulur.
    """
    return entry_tint_seconds + freq_error_estimate * max(0.0, elapsed_seconds)
