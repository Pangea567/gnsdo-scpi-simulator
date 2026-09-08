"""
models/noise.py

DETERMINISTIK OLCUM GURULTUSU.

PROBLEM:
  Gercek bir cihazda MEAS:TEMP? her sorguda tipatip ayni sayiyi
  dondurmez -- sensor okumasi son hanede surekli oynar. Simulator
  sabit deger dondurunce bu "sahtelik" hemen belli olur.

AKLA ILK GELEN COZUM VE NICIN YANLIS:
  "Her sorguda random.gauss() cagiralim" demek cazip ama iki
  bakimdan hatali:

  1. FIZIKSEL OLARAK SACMA. Cihazin sicakligi BELLI BIR ANDA belli
     bir degerdir. Ayni saniye icinde iki kez sorarsan ayni cevabi
     almalisin. Rastgele akista ise deger, KAC KEZ SORDUGUNA bagli
     olur -- sanki sen sordukca cihazin sicakligi degisiyormus gibi.

  2. TEKRARLANABILIR DEGIL. Bir hata gordugunde ayni kosulu yeniden
     uretemezsin; hata ayiklama imkansizlasir.

BIZIM YAKLASIMIMIZ -- GURULTU ZAMANIN FONKSIYONUDUR:

      deger(t) = taban + genlik * smooth_noise(t)

  t = simulator acildigindan beri gecen sure. Bu tek degisiklik uc
  seyi birden saglar:
    - Ayni calistirma      -> ayni degerler (tekrarlanabilir)
    - Ayni anda iki sorgu  -> ayni cevap (fiziksel olarak dogru)
    - Zaman ilerledikce    -> yumusak salinim (gercekci)

  DIKKAT: t, DUVAR SAATI degil, PROGRAM BASLANGICINDAN beri gecen
  suredir. Duvar saati kullansaydik iki farkli gunde calistirilan
  ayni senaryo farkli degerler uretirdi -- tekrarlanabilirlik giderdi.

NASIL URETILIYOR:
  Birbirine orani IRRASYONEL olan birkac sinusun toplami. Neden
  irrasyonel? Cunku oranlar tam sayi olsaydi desen kisa surede
  tekrarlardi ve gozle fark edilen bir periyodiklik olusurdu.
  Altin oran (1.618...) kullaniyoruz: tekrar suresi pratikte
  sonsuza gider, sonuc "gezinen" bir sensor okumasi gibi gorunur.

  Bu yontem kutuphane gerektirmez, DURUM TUTMAZ (her cagri bagimsiz
  hesaplanir) ve tam deterministiktir.
"""

import math

# Altin oran. Sinus bilesenlerinin frekans oranlarini irrasyonel
# yapmak icin kullaniyoruz -- boylece desen kendini tekrarlamaz.
GOLDEN_RATIO = 1.6180339887498949

# (agirlik, frekans carpani) ciftleri. Agirligi buyuk olan bilesen
# yavas ve genis salinimi, kucukler ise uzerine binen ince
# titresimleri verir -- gercek sensor gurultusu de boyle katmanlidir.
_COMPONENTS = (
    (1.00, 1.0),
    (0.50, GOLDEN_RATIO),
    (0.25, GOLDEN_RATIO**2),
)

_WEIGHT_SUM = sum(weight for weight, _ in _COMPONENTS)


def _seed_phase(seed) -> float:
    """
    Bir tohumdan (sayi ya da metin) deterministik bir faz kaymasi
    uretir. Her olcum alaninin FARKLI bir tohum kullanmasi sayesinde
    sicaklik, voltaj ve akim ayni anda ayni yone gitmez -- aksi halde
    hepsi senkronize salinir ve yapay gorunurdu.

    NICIN Python'un hash() FONKSIYONUNU KULLANMIYORUZ:
      Python, metinler icin hash()'i her calistirmada RASTGELE
      tohumlar (guvenlik onlemi). Yani hash("temperature") her
      calistirmada farkli cikar ve determinizm kaybolurdu. Bu yuzden
      kendi kucuk, sabit hesabimizi yapiyoruz.
    """
    if isinstance(seed, str):
        h = 0
        for ch in seed:
            h = (h * 31 + ord(ch)) % 1000003
        seed = h

    return (int(seed) % 1000) * 2.0 * math.pi / 1000.0


def smooth_noise(elapsed_seconds: float, seed=0, period: float = 60.0) -> float:
    """
    -1 ile +1 arasinda, zamanla YUMUSAK degisen deterministik bir
    deger uretir.

    Parametreler:
        elapsed_seconds -- program baslangicindan beri gecen sure
        seed            -- alan basina farkli desen icin tohum
                           (ornegin "temperature", "voltage")
        period          -- en yavas bilesenin periyodu (saniye).
                           Kucuk deger = hizli titresim (elektriksel
                           gurultu), buyuk deger = yavas gezinme
                           (isil kutle nedeniyle sicaklik).

    Ayni girdilerle HER ZAMAN ayni sonucu dondurur.
    """
    phase = _seed_phase(seed)

    total = 0.0
    for weight, freq_multiplier in _COMPONENTS:
        angle = (
            2.0 * math.pi * freq_multiplier * elapsed_seconds / period
            + phase * freq_multiplier
        )
        total += weight * math.sin(angle)

    return total / _WEIGHT_SUM
