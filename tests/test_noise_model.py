"""
test_noise_model.py

Deterministik olcum gurultusu modeli (models/noise.py) icin testler.

Buradaki testlerin cogu "gurultu dogru gorunuyor mu" degil,
"gurultu DETERMINISTIK ve FIZIKSEL olarak tutarli mi" sorusunu
sorar -- cunku modelin asil degeri budur.

pytest calistirmak icin (repo kok dizininden):
    pytest tests/test_noise_model.py -v
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gnsdo_simulator.models.noise import GOLDEN_RATIO, smooth_noise


def test_ayni_girdi_ayni_cikti():
    """
    Determinizmin TANIMI: ayni girdi hep ayni cikti.

    Bu saglanmazsa hata ayiklama imkansiz hale gelir -- bir sorunu
    gordugunde ayni kosulu yeniden uretemezsin.
    """
    for t in [0, 1.5, 42.0, 1000.0]:
        assert smooth_noise(t, "temperature", 60) == smooth_noise(
            t, "temperature", 60
        )


def test_ayni_anda_iki_sorgu_ayni_degeri_verir():
    """
    FIZIKSEL GEREKLILIK: cihazin sicakligi belli bir ANDA belli bir
    degerdir. Ayni anda iki kez sorman sonucu degistirmemeli.

    Bu test, "her sorguda random.gauss() cagir" yaklasimini elerdi --
    o yaklasim bu testi gecemez. Gurultunun ZAMANIN FONKSIYONU
    olmasinin sebebi tam olarak budur.
    """
    an = 123.456
    okumalar = [smooth_noise(an, "voltage", 10) for _ in range(5)]
    assert len(set(okumalar)) == 1


def test_deger_araligi_sinirli():
    """
    Cikti -1 ile +1 arasinda kalmali. Kalmazsa genlik hesabi
    bozulur ve olcumler gercekci olmayan degerlere sicrar.
    """
    for i in range(5000):
        deger = smooth_noise(i * 0.37, "test", 60)
        assert -1.0 <= deger <= 1.0


def test_farkli_tohumlar_farkli_desen_uretir():
    """
    Her olcum alani FARKLI bir tohum kullanmali, yoksa sicaklik,
    voltaj ve akim ayni anda ayni yone gider -- gozle bakildiginda
    hemen yapay oldugu anlasilir.
    """
    t = 50.0
    sicaklik = smooth_noise(t, "temperature", 60)
    voltaj = smooth_noise(t, "voltage", 60)
    akim = smooth_noise(t, "current", 60)

    assert sicaklik != voltaj
    assert voltaj != akim


def test_metin_tohum_calistirmalar_arasinda_kararli():
    """
    KRITIK: Python metinler icin hash()'i her calistirmada RASTGELE
    tohumlar (guvenlik onlemi). Eger _seed_phase() Python'un hash()
    fonksiyonunu kullansaydi, "temperature" tohumu her calistirmada
    farkli faz uretir ve determinizm SESSIZCE kaybolurdu.

    Bu test o tuzagi yakalar: bilinen bir girdi icin sonucu sabitler.
    Deger degisirse ya algoritma degismistir ya da hash sizmistir.

    Asagidaki sayi, AYRI SURECLERDE calistirilarak dogrulandi --
    Python'un hash rastgeleligi sizmis olsaydi her surecte farkli
    cikardi.
    """
    deger = smooth_noise(100.0, "temperature", 60.0)
    assert deger == pytest.approx(-0.7200314338, abs=1e-9)


def test_zamanla_yumusak_degisir_sicramaz():
    """
    Gercek bir sensor okumasi ani sicramalar yapmaz. Ardisik
    orneklemeler arasindaki fark kucuk olmali.

    Bu test "yumusaklik" ozelligini korur: biri gunun birinde modeli
    saf rastgeleyle degistirirse burasi patlar.
    """
    onceki = smooth_noise(0.0, "temperature", 300.0)
    for i in range(1, 200):
        simdiki = smooth_noise(i * 0.5, "temperature", 300.0)
        # 0.5 saniyede, 300 saniyelik periyotta, degisim kucuk olmali
        assert abs(simdiki - onceki) < 0.05
        onceki = simdiki


def test_periyot_salinim_hizini_belirler():
    """
    Kisa periyot = hizli titresim (elektriksel gurultu),
    uzun periyot = yavas gezinme (isil kutle nedeniyle sicaklik).

    Ayni sure icinde kisa periyotlu sinyal daha cok yol katetmeli.
    """

    def toplam_degisim(period):
        degerler = [smooth_noise(i * 0.5, "x", period) for i in range(120)]
        return sum(abs(b - a) for a, b in zip(degerler, degerler[1:]))

    hizli = toplam_degisim(5.0)
    yavas = toplam_degisim(600.0)
    assert hizli > yavas * 10


def test_desen_kisa_surede_tekrarlamaz():
    """
    Frekans oranlari IRRASYONEL secildigi icin (altin oran) desen
    kendini pratik surelerde tekrarlamamali. Tam sayi oranlari
    kullansaydik gozle fark edilen bir periyodiklik olusurdu.
    """
    period = 60.0
    baslangic = smooth_noise(0.0, "x", period)

    # Bir "periyot" sonra ayni degere DONMEMELI -- cunku diger iki
    # bilesen irrasyonel oranlarla baska noktalarda
    assert smooth_noise(period, "x", period) != pytest.approx(baslangic, abs=1e-6)


def test_altin_oran_gercekten_irrasyonel_yaklasimi():
    """
    Kullandigimiz sabitin gercekten altin oran oldugunu dogrular:
    phi^2 = phi + 1 ozelligini saglamali.

    Yanlis bir sabit (ornegin 1.5) kullanilirsa desen tekrarlamaya
    baslar; bu test onu yakalar.
    """
    assert GOLDEN_RATIO**2 == pytest.approx(GOLDEN_RATIO + 1, abs=1e-12)
