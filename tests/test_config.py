"""
test_config.py

config_loader.py icin testler -- YAML dosyalarinin dogru okunup
DeviceState'e dogru uygulandigini kanitlar.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from gnsdo_simulator.config_loader import load_scenario
from gnsdo_simulator.device_state import is_locked, WARMUP_DURATION_SECONDS


# Testler repo kok dizininden calistirilacagi icin (pytest tests/ -v),
# "configs/" gorece (relative) yolu dogru calisir.
CONFIGS_DIR = "configs"


def test_load_normal_scenario():
    state = load_scenario("normal", configs_dir=CONFIGS_DIR)
    assert state.gnss_satellites_tracking == 8
    assert state.gnss_satellites_visible == 12
    assert state.sync_locked is True
    assert state.holdover is False


def test_load_gnss_lost_scenario():
    state = load_scenario("gnss-lost", configs_dir=CONFIGS_DIR)
    assert state.gnss_satellites_tracking == 0
    assert state.gnss_satellites_visible == 0
    assert state.sync_locked is False


def test_load_holdover_scenario_sets_holdover_started_at():
    """
    holdover: true olan bir senaryo yuklendiginde, holdover_started_at
    otomatik olarak (config'te belirtilmedigi halde) "simdi" olarak
    ayarlanmali -- yoksa SYNC:HOLD:DUR? calismaz.
    """
    state = load_scenario("holdover", configs_dir=CONFIGS_DIR)
    assert state.holdover is True
    assert state.sync_locked is False
    assert state.holdover_started_at is not None


def test_unknown_scenario_raises():
    """
    Var olmayan bir senaryo istenirse, sessizce bos bir state
    donmek yerine ACIK bir hata vermeliyiz -- yoksa kullanici
    yazim hatasi yaptiginda (ornegin "--scenario nromal") sebebini
    anlamakta zorlanir.
    """
    with pytest.raises(FileNotFoundError):
        load_scenario("boyle-bir-senaryo-yok", configs_dir=CONFIGS_DIR)


def test_load_warming_up_scenario():
    """
    warming-up senaryosu artik warmup_started_at ile isaretleniyor.
    Yeni yuklendiginde HENUZ kilitli olmamali (gercek cihazin 2
    dakikalik isinma suresi henuz gecmedi), ama is_locked()
    fonksiyonu bunu ZAMANLA otomatik degistirecek sekilde kurulu
    olmali.
    """
    state = load_scenario("warming-up", configs_dir=CONFIGS_DIR)
    assert state.warmup_started_at is not None
    assert is_locked(state) is False  # daha yeni yuklendi, 2 dk gecmedi
    assert state.diag_lifetime_base_hours == 0
    # ONEMLI: tracking artik esigin (4) USTUNDE -- GPS fix'i VAR,
    # sadece osilator henuz isiniyor. (Once tracking=3 idi, bu
    # is_locked()'in "fix yoksa kilitlenemez" kuraliyla CELISIYORDU.)
    assert state.gnss_satellites_tracking == 8


def test_warming_up_locks_after_warmup_duration():
    """
    Gercek cihazin kilavuzuna gore ("less than 2 minutes warmup") --
    WARMUP_DURATION_SECONDS kadar sure gectikten SONRA, is_locked()
    OTOMATIK olarak True donmeli. Burada gercekten 120 saniye
    beklemek yerine, warmup_started_at'i GECMISE cekerek (sanki
    2 dakika once baslamis gibi) ayni sonucu test ediyoruz.
    """
    from datetime import datetime, timedelta

    state = load_scenario("warming-up", configs_dir=CONFIGS_DIR)
    state.warmup_started_at = datetime.now() - timedelta(seconds=WARMUP_DURATION_SECONDS + 1)
    assert is_locked(state) is True


def test_load_not_locked_scenario():
    state = load_scenario("not-locked", configs_dir=CONFIGS_DIR)
    assert state.sync_locked is False
    assert state.warmup_started_at is None  # bu bir isinma degil, kalici sorun
    # not-locked'i warming-up'tan ayiran fark: lifetime SIFIR DEGIL
    assert state.diag_lifetime_base_hours == 871
    # GPS sinyali gayet iyi, sorun kilitlenmede -- GPS'te degil
    assert state.gnss_satellites_tracking == 8
    # ONEMLI: not-locked bir DONANIM ARIZASI DEGIL. (Onceden bu config
    # yanlislikla hardware-error.yaml'in kopyasiydi, fault=true iceriyordu
    # ve SYST:STAT? "Fault" donuyordu. Bu assert o hatanin geri gelmesini
    # engeller.)
    assert state.hardware_fault is False
    assert state.temperature_celsius == 42.5   # normal deger, ariza degeri (95.0) DEGIL


def test_not_locked_scenario_reports_not_locked_status():
    """
    not-locked senaryosu SYST:STAT?'ta "Not Locked" durumunu gostermeli --
    "Fault" DEGIL. (Config'in hardware-error kopyasi olmasi hatasina karsi
    ucdan uca / end-to-end kontrol.)
    """
    from gnsdo_simulator.scpi_parser import SCPIParser
    from gnsdo_simulator.commands.system import register_system_commands

    state = load_scenario("not-locked", configs_dir=CONFIGS_DIR)
    parser = SCPIParser()
    register_system_commands(parser, state)
    assert "GPSDO Status : Not Locked" in parser.dispatch("SYST:STAT?")


def test_load_hardware_error_scenario():
    state = load_scenario("hardware-error", configs_dir=CONFIGS_DIR)
    assert state.hardware_fault is True
    assert state.fault_message == "OSCILLATOR FAILURE"

def test_holdover_scenario_loads_model_parameters():
    """
    holdover.yaml'daki hata birikimi modeli parametreleri gercekten
    DeviceState'e ulasmali. Bu parametreler config'ten okunmazsa model
    sessizce varsayilan degerlerle calisir ve senaryoyu ayarlamak
    imkansiz hale gelir -- bu tur "sessiz duserek calisma" hatalarini
    yakalamak icin bu test var.
    """
    state = load_scenario("holdover")

    assert state.freq_error_estimate == 1.31e-11  # y0, kilavuz §3.6.10
    assert state.locked_tint_seconds == 1.2e-08  # x0 kaynagi, §1.1
    assert state.rb_drift_per_day == 8.0e-14  # D, kilavuz §2.9


def test_holdover_entry_tint_frozen_from_locked_value():
    """
    KRITIK SIRA KONTROLU: config_loader, model parametrelerini
    "holdover: true" bayragindan ONCE okumali.

    Cunku enter_holdover(), holdover'a girerken TINT'i (modelin x0'i)
    locked_tint_seconds'tan kopyalar. Sira ters olsaydi holdover
    VARSAYILAN degerle baslar, config'teki locked_tint yok sayilirdi
    -- ve bu sessizce olurdu, hicbir hata vermeden.
    """
    state = load_scenario("holdover")

    assert state.holdover is True
    assert state.holdover_entry_tint_seconds == state.locked_tint_seconds


def test_holdover_scenario_tint_accumulates_over_time():
    """
    Senaryonun ASIL amaci: holdover'da TINT zamanla BUYUMELI.

    Gercek zamanda beklemek yerine holdover baslangicini geriye
    tarihliyoruz -- boylece "1 saat gecmis olsa ne olurdu?" sorusunu
    aninda sorabiliyoruz.
    """
    from datetime import datetime, timedelta

    from gnsdo_simulator.device_state import current_tint_seconds

    state = load_scenario("holdover")

    # Bu testin konusu BIRIKIM; olcum jitter'i sayilari bulandirmasin
    # diye gurultuyu kapatiyoruz (jitter ayri testlerde dogrulaniyor).
    state.noise_scale = 0.0

    # Holdover henuz yeni basladi: TINT giris degerine cok yakin olmali
    baslangic = current_tint_seconds(state)
    assert baslangic == pytest.approx(state.locked_tint_seconds, rel=1e-3)

    # 1 saat geriye tarihle: y0 * 3600 = 1.31e-11 * 3600 = 47.16 ns
    # birikmis olmali (buna giristeki ~12 ns ekleniyor)
    state.holdover_started_at = datetime.now() - timedelta(hours=1)
    bir_saat_sonra = current_tint_seconds(state)
    assert bir_saat_sonra == pytest.approx(
        state.locked_tint_seconds + 1.31e-11 * 3600, rel=1e-3
    )

    # 5 saat geriye tarihle: 210 ns'lik saglik esigi (§3.6.18) asilmali
    state.holdover_started_at = datetime.now() - timedelta(hours=5)
    assert abs(current_tint_seconds(state)) > 210e-9
