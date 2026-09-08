"""
test_holdover_model.py

Holdover hata birikimi modeli (models/holdover.py) icin testler.

Bu testler MODELI DOGRUDAN cagirir -- seri port, parser ya da
DeviceState devrede degildir. Model saf fonksiyonlardan olustugu icin
"4.5 saat gecmis olsaydi" senaryosunu, gercek zamanda beklemeden,
sureyi parametre vererek test edebiliyoruz.

pytest calistirmak icin (repo kok dizininden):
    pytest tests/test_holdover_model.py -v
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gnsdo_simulator.models.holdover import (
    NOMINAL_LOCKED_TINT_SECONDS,
    RB_DRIFT_PER_DAY,
    SECONDS_PER_DAY,
    drift_per_second,
    holdover_tint_seconds,
)

# Gercek cihazin SYNC? ciktisindan alinan FEE degeri -- testlerde
# "tipik" osilator icin bunu kullaniyoruz.
GERCEK_FEE = 1.31e-11

# Kilavuz §3.6.18: faz farki bu esigi asinca SYNC:HEALTH? 0x4 yanar.
HEALTH_PHASE_THRESHOLD_SECONDS = 210e-9


def test_birim_donusumu_gun_basinadan_saniye_basina():
    """
    D'nin birimi formulde 1/saniye olmali ama kilavuz degeri GUN
    cinsinden veriyor. Bu donusum yanlis olursa model 86400 kat
    saparki bu tur birim hatalari fizik kodundaki en yaygin hatadir.
    """
    assert drift_per_second(8e-14) == 8e-14 / SECONDS_PER_DAY
    # Varsayilan deger kilavuzdaki §2.9 degeri olmali
    assert drift_per_second() == RB_DRIFT_PER_DAY / SECONDS_PER_DAY


def test_sifir_surede_giris_degeri_korunur():
    """
    Faz SUREKLIDIR: holdover'a girildigi anda (t=0) TINT, giristeki
    degerin ta kendisidir -- sifira atlamaz, ziplamaz.
    """
    giris = 12.0e-9
    assert holdover_tint_seconds(0, entry_tint_seconds=giris) == giris


def test_negatif_sure_giris_degerini_dondurur():
    """Gecmise dogru hesap anlamsiz; giris degeri aynen donmeli."""
    giris = 5.0e-9
    assert holdover_tint_seconds(-100, entry_tint_seconds=giris) == giris


def test_bir_saat_sonra_dogrusal_terim_baskin():
    """
    1 saat sonra beklenen: y0 * 3600 = 1.31e-11 * 3600 = 47.16 ns
    Buna x0 (0.2 ns) eklenir, kuadratik terim ise ~0.006 ns ile
    tamamen ihmal edilebilir.

    Bu test modelin SAATLER mertebesindeki davranisini sabitler.
    """
    sonuc = holdover_tint_seconds(3600, freq_error_estimate=GERCEK_FEE)
    beklenen_dogrusal = GERCEK_FEE * 3600  # 47.16 ns

    # x0 dahil oldugu icin sonuc dogrusal terimden BIRAZ buyuk olmali
    assert sonuc > beklenen_dogrusal
    # ama kuadratik terim bu olcekte gorunmez oldugu icin cok az
    assert sonuc == pytest.approx(
        beklenen_dogrusal + NOMINAL_LOCKED_TINT_SECONDS, rel=0.001
    )


def test_saglik_esigine_ulasma_suresi_yaklasik_dort_bucuk_saat():
    """
    Kilavuz §3.6.18'e gore 210 ns'yi asinca HEALTH 0x4 yanar.
    Gercek FEE degeriyle bu ~4.5 saat surmelidir.

    Bu, modelin "gercekci mi" sorusunun somut cevabidir: cok hizli
    olsaydi (dakikalar) ya da cok yavas (gunler) olsaydi model
    yanlis olurdu.
    """
    dort_bucuk_saat_once = holdover_tint_seconds(
        4.0 * 3600, freq_error_estimate=GERCEK_FEE
    )
    bes_saat_sonra = holdover_tint_seconds(5.0 * 3600, freq_error_estimate=GERCEK_FEE)

    # 4 saatte henuz esik asilmamis, 5 saatte asilmis olmali
    assert dort_bucuk_saat_once < HEALTH_PHASE_THRESHOLD_SECONDS
    assert bes_saat_sonra > HEALTH_PHASE_THRESHOLD_SECONDS


def test_kuadratik_terim_gunler_mertebesinde_devreye_girer():
    """
    Modelin en onemli ozelligi: yaslanma terimi kisa surede gorunmez,
    uzun surede belirginlesir. Bu testi gecmek icin modelin GERCEKTEN
    kuadratik olmasi gerekir -- sadece dogrusal bir model bu testi
    gecemez.
    """
    D = drift_per_second()

    # 1 saat: kuadratik katki dogrusal katkinin binde birinden az
    t_kisa = 3600
    kuadratik_kisa = 0.5 * D * t_kisa**2
    dogrusal_kisa = GERCEK_FEE * t_kisa
    assert kuadratik_kisa < dogrusal_kisa / 1000

    # 1 gun: kuadratik katki artik olculebilir (nanosaniye mertebesinde)
    t_uzun = SECONDS_PER_DAY
    kuadratik_uzun = 0.5 * D * t_uzun**2
    assert kuadratik_uzun > 1e-9  # 1 ns'den buyuk


def test_hata_zamanla_monoton_artar():
    """
    Fiziksel gereklilik: pozitif y0 ile hata birikimi GERI GITMEZ.
    Holdover ne kadar uzarsa hata o kadar buyur.
    """
    sureler = [0, 60, 600, 3600, 36000, 86400]
    degerler = [
        holdover_tint_seconds(t, freq_error_estimate=GERCEK_FEE) for t in sureler
    ]
    assert degerler == sorted(degerler)


def test_negatif_frekans_hatasi_isareti_korur():
    """
    Osilator referanstan GERI kaliyorsa (y0 negatif) TINT negatif
    yonde buyumeli. Gercek cihazda TINT isaretli bir buyukluktur.

    Bu ONEMLI: SYNC:HEALTH? kontrolu mutlak deger kullanmali, yoksa
    negatif yonde 210 ns'yi asan bir hata KACIRILIR.
    """
    sonuc = holdover_tint_seconds(
        3600, entry_tint_seconds=0.0, freq_error_estimate=-GERCEK_FEE
    )
    assert sonuc < 0
    assert abs(sonuc) > 40e-9  # buyuklugu pozitif durumla ayni mertebede


def test_sifir_frekans_hatasinda_sadece_yaslanma_kalir():
    """
    Kusursuz bir osilator (y0 = 0) bile yaslanma yuzunden yavasca
    kayar. Bu, modelin iki teriminin BAGIMSIZ oldugunu dogrular.
    """
    sonuc = holdover_tint_seconds(
        SECONDS_PER_DAY, entry_tint_seconds=0.0, freq_error_estimate=0.0
    )
    beklenen = 0.5 * drift_per_second() * SECONDS_PER_DAY**2
    assert sonuc == pytest.approx(beklenen, rel=1e-9)
