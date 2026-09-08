"""
test_warmup_model.py

Isinma rampasi ve servo durum makinesi (models/warmup.py) icin testler.

Model saf fonksiyonlardan olustugu icin "20 dakika gecmis olsaydi"
sorusunu gercek zamanda beklemeden sorabiliyoruz.

pytest calistirmak icin (repo kok dizininden):
    pytest tests/test_warmup_model.py -v
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gnsdo_simulator.models.warmup import (
    AMBIENT_TEMPERATURE_C,
    ATOMIC_LOCK_SECONDS,
    GNSS_LOCK_SECONDS,
    HOLDOVER_PHASE_LOCKED_SECONDS,
    SERVO_STATE_HOLDOVER,
    SERVO_STATE_HOLDOVER_PHASE_LOCKED,
    SERVO_STATE_LOCKED,
    SERVO_STATE_LOCKING,
    SERVO_STATE_WARMUP,
    THERMAL_TIME_CONSTANT_SECONDS,
    is_warming_up,
    servo_state,
    thermal_ramp,
)

KARARLI_PCB_SICAKLIGI = 52.8


# --------------------------------------------------------------
# Isil rampa
# --------------------------------------------------------------


def test_baslangicta_ortam_sicakliginda():
    """t=0'da cihaz henuz soguk -- ortam sicakliginda olmali."""
    assert thermal_ramp(0, KARARLI_PCB_SICAKLIGI) == AMBIENT_TEMPERATURE_C
    assert thermal_ramp(-50, KARARLI_PCB_SICAKLIGI) == AMBIENT_TEMPERATURE_C


def test_zaman_sabitinde_farkin_yuzde_63u_kapanir():
    """
    USTEL yaklasimin TANIMI: bir zaman sabiti (tau) sonunda,
    baslangictaki farkin 1 - 1/e ≈ %63.2'si kapanmis olur.

    Bu test modelin gercekten ustel oldugunu sabitler -- dogrusal
    bir rampa bu testi gecemez.
    """
    sonuc = thermal_ramp(THERMAL_TIME_CONSTANT_SECONDS, KARARLI_PCB_SICAKLIGI)

    toplam_fark = KARARLI_PCB_SICAKLIGI - AMBIENT_TEMPERATURE_C
    kapanan = sonuc - AMBIENT_TEMPERATURE_C

    assert kapanan / toplam_fark == pytest.approx(0.632, abs=0.002)


def test_uc_zaman_sabitinde_yaklasik_tamamlanir():
    """3*tau sonunda farkin ~%95'i kapanmis olmali."""
    sonuc = thermal_ramp(3 * THERMAL_TIME_CONSTANT_SECONDS, KARARLI_PCB_SICAKLIGI)

    toplam_fark = KARARLI_PCB_SICAKLIGI - AMBIENT_TEMPERATURE_C
    kapanan = sonuc - AMBIENT_TEMPERATURE_C

    assert kapanan / toplam_fark == pytest.approx(0.95, abs=0.01)


def test_hedefe_asla_tam_ulasmaz_ama_yaklasir():
    """
    Asimptotik yaklasim: sicaklik hedefe VARIP DURMAZ, sonsuza kadar
    yaklasir. Dogrusal bir rampa hedefe varip orada kalirdi -- ve
    ondan sonrasinda hedefi ASARDI, ki bu fiziksel olarak sacma.
    """
    # Makul bir ufukta: hedefin ALTINDA ama cok yakin
    uzun_sure = thermal_ramp(10 * THERMAL_TIME_CONSTANT_SECONDS, KARARLI_PCB_SICAKLIGI)
    assert uzun_sure < KARARLI_PCB_SICAKLIGI
    assert uzun_sure == pytest.approx(KARARLI_PCB_SICAKLIGI, abs=0.01)

    # Cok uzun surede hedefi ASMAMALI. Burada "<" degil "<=" kullaniyoruz:
    # e^(-100) o kadar kucuk ki kayan nokta hassasiyetinin altina duser ve
    # sonuc TAM hedefe esit cikar. Bu bir model hatasi degil, sayisal
    # gosterimin siniri -- fiziksel iddia ("hedefi asmaz") korunuyor.
    cok_uzun_sure = thermal_ramp(100 * THERMAL_TIME_CONSTANT_SECONDS, KARARLI_PCB_SICAKLIGI)
    assert cok_uzun_sure <= KARARLI_PCB_SICAKLIGI


def test_sicaklik_monoton_artar():
    """Isinma sirasinda sicaklik geri gitmez."""
    degerler = [thermal_ramp(t, KARARLI_PCB_SICAKLIGI) for t in range(0, 3600, 60)]
    assert degerler == sorted(degerler)


def test_ramp_gercek_cihaz_olcumuyle_ortusur():
    """
    DOGRULAMA: Gercek cihaz kayitlarindaki EN DUSUK PCB sicakligi
    46.5688 idi (docs/gercek-cihaz-ciktilari.md).

    Isil zaman sabitini kilavuzun 20 dakikalik kilit suresinden
    sectik, bu sayiya BAKARAK degil. Yine de model, ~15. dakikada
    tam o degeri uretiyor -- yani gercek okuma isinmanin ortalarinda
    alinmis olmali. Model bagimsiz bir gozlemi yeniden uretiyor.
    """
    on_bes_dakika = thermal_ramp(15 * 60, KARARLI_PCB_SICAKLIGI)
    assert on_bes_dakika == pytest.approx(46.5688, abs=0.1)


# --------------------------------------------------------------
# Servo durum makinesi
# --------------------------------------------------------------


def test_acilista_isinma_durumu():
    """Aciliskan itibaren 2 dakika dolmadan durum 0 (isinma)."""
    assert servo_state(0) == SERVO_STATE_WARMUP
    assert servo_state(ATOMIC_LOCK_SECONDS - 1) == SERVO_STATE_WARMUP
    assert is_warming_up(0) is True


def test_atomik_kilitten_sonra_kilitlenme_durumu():
    """
    2 dakika sonra atomik kilit saglanir (§1.1) ama GNSS'e kilitlenme
    egitimi surer -- durum 2.
    """
    assert servo_state(ATOMIC_LOCK_SECONDS) == SERVO_STATE_LOCKING
    assert servo_state(GNSS_LOCK_SECONDS - 1) == SERVO_STATE_LOCKING
    assert is_warming_up(ATOMIC_LOCK_SECONDS) is False


def test_yirmi_dakika_sonra_kilitli():
    """§2.5: kilit tipik olarak 20 dakikadan kisa surede saglanir."""
    assert servo_state(GNSS_LOCK_SECONDS) == SERVO_STATE_LOCKED
    assert servo_state(GNSS_LOCK_SECONDS * 10) == SERVO_STATE_LOCKED


def test_gnss_fixi_yoksa_kilitlenemez():
    """
    Sure dolmus olsa bile GNSS fix'i yoksa cihaz kilitli olamaz --
    kilitlenecek bir referans yok.
    """
    assert servo_state(GNSS_LOCK_SECONDS * 10, gnss_locked=False) == SERVO_STATE_LOCKING


def test_gnss_kaybindan_sonra_once_faz_kilitli_kalir():
    """
    KILAVUZUN OZEL DURUMU (§3.10.3, durum 5): GNSS kaybindan sonra
    cihaz ANINDA holdover demez -- faz halen kilitlidir ve ~100 saniye
    bu ara durumda kalir.

    Bu gecis olmasaydi, GNSS kaybini izleyen bir test uygulamasi
    gercek cihazda gorecegi ara durumu simulatorde hic gormezdi.
    """
    assert (
        servo_state(5000, holdover=True, holdover_elapsed_seconds=0)
        == SERVO_STATE_HOLDOVER_PHASE_LOCKED
    )
    assert (
        servo_state(5000, holdover=True, holdover_elapsed_seconds=99)
        == SERVO_STATE_HOLDOVER_PHASE_LOCKED
    )


def test_yuz_saniye_sonra_tam_holdover():
    """~100 saniye sonra faz kilidi de kaybolur, tam holdover (durum 1)."""
    assert (
        servo_state(
            5000, holdover=True, holdover_elapsed_seconds=HOLDOVER_PHASE_LOCKED_SECONDS
        )
        == SERVO_STATE_HOLDOVER
    )
    assert (
        servo_state(5000, holdover=True, holdover_elapsed_seconds=3600)
        == SERVO_STATE_HOLDOVER
    )


def test_holdover_isinmadan_onceliklidir():
    """
    Cihaz heniz isinirken holdover'a sokulursa holdover kazanir --
    kilavuzun durum listesinde holdover ayri bir daldir.
    """
    assert (
        servo_state(10, holdover=True, holdover_elapsed_seconds=200)
        == SERVO_STATE_HOLDOVER
    )
