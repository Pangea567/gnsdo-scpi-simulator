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


def test_warming_up_progresses_through_servo_states():
    """
    Isinma TEK ADIMDA degil, KADEMELI olur.

    DEGISTI: Bu test eskiden "120 saniye sonra kilitli" diyordu. O sure
    kilavuz §1.1'deki ATOMIK kilit suresidir ("less than 2 minutes
    warmup time to atomic lock") -- ama SYNC:LOCKED?, §3.6.11'e gore
    ATOMIK kilidi degil, Rubidyum osilatoru kontrol eden PLL'in yani
    GNSS'e KILITLENMENIN durumunu bildirir. O ise §2.5'e gore tipik
    olarak 20 dakika surer.

    Yani eski test yanlis bir esik kullaniyordu: cihaz 2 dakikada
    "atomik kilit" saglar ama heniz GNSS'e kilitli DEGILDIR -- arada
    "kilitleniyor" (durum 2) diye gercek bir asama vardir.
    """
    from datetime import datetime, timedelta

    from gnsdo_simulator.device_state import current_servo_state
    from gnsdo_simulator.models.warmup import (
        ATOMIC_LOCK_SECONDS,
        GNSS_LOCK_SECONDS,
        SERVO_STATE_LOCKED,
        SERVO_STATE_LOCKING,
        SERVO_STATE_WARMUP,
    )

    state = load_scenario("warming-up", configs_dir=CONFIGS_DIR)

    def zamani_ayarla(saniye):
        state.warmup_started_at = datetime.now() - timedelta(seconds=saniye)

    # 1) Ilk 2 dakika: isinma, kilit yok
    zamani_ayarla(10)
    assert current_servo_state(state) == SERVO_STATE_WARMUP
    assert is_locked(state) is False

    # 2) Atomik kilit sonrasi: kilitleniyor, ama HENIZ kilitli degil
    zamani_ayarla(ATOMIC_LOCK_SECONDS + 1)
    assert current_servo_state(state) == SERVO_STATE_LOCKING
    assert is_locked(state) is False

    zamani_ayarla(GNSS_LOCK_SECONDS - 10)
    assert current_servo_state(state) == SERVO_STATE_LOCKING
    assert is_locked(state) is False

    # 3) ~20 dakika sonra: gercek GNSS kilidi
    zamani_ayarla(GNSS_LOCK_SECONDS + 1)
    assert current_servo_state(state) == SERVO_STATE_LOCKED
    assert is_locked(state) is True


def test_warming_up_temperature_climbs():
    """
    Isinma sirasinda sicaklik ORTAM SICAKLIGINDAN baslayip kararli
    calisma sicakligina tirmanmali -- ve bu tirmanis ustel olmali.
    """
    from datetime import datetime, timedelta

    from gnsdo_simulator.device_state import measured_temperature

    state = load_scenario("warming-up", configs_dir=CONFIGS_DIR)
    state.noise_scale = 0.0

    # Isinma hizli oldugu icin erken zamanlarda ornekliyoruz (5 dk'da
    # neredeyse doymus olur).
    okumalar = []
    for dakika in [0, 0.5, 1, 2, 5]:
        state.warmup_started_at = datetime.now() - timedelta(minutes=dakika)
        okumalar.append(measured_temperature(state))

    # Baslangicta ortam sicakliginda
    assert okumalar[0] == pytest.approx(state.ambient_temperature_c, abs=0.1)
    # Monoton artmali
    assert okumalar == sorted(okumalar)
    # Kararli degeri ASMAMALI
    assert okumalar[-1] < state.temperature_celsius
    # USTEL: erken artis (0->0.5dk) gec artistan (2->5dk) BUYUK olmali
    ilk_artis = okumalar[1] - okumalar[0]
    son_artis = okumalar[4] - okumalar[3]
    assert ilk_artis > son_artis


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
    # Normal kararli sicaklik (gercek cihaz kayitlarindan),
    # ariza degeri (95.0) DEGIL
    assert state.temperature_celsius == 52.8


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

    assert state.freq_error_estimate == 1.8e-11  # y0, kilavuz §3.6.10
    # DUZELTILDI: taban artik SIFIR -- gercek cihazda TINT sifirin
    # etrafinda salinir, sabit pozitif offseti yoktur
    assert state.locked_tint_seconds == 0.0
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

    # Giris degeri, holdover'a girildigi andaki ANLIK okumadir
    # (jitter dahil), taban deger degil -- faz sureklidir, o an
    # sayac neyi gosteriyorsa birikim oradan baslar.
    # Jitter bandi +/-12 ns oldugundan giris degeri de o bantta olmali.
    assert abs(state.holdover_entry_tint_seconds) < 15e-9


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

    # Holdover henuz yeni basladi: TINT, DONDURULAN giris degerine
    # esit olmali
    giris = state.holdover_entry_tint_seconds
    baslangic = current_tint_seconds(state)
    assert baslangic == pytest.approx(giris, abs=1e-12)

    # 1 saat geriye tarihle: y0 * 3600 kadar birikmis olmali
    # (giris degerinin USTUNE). y0 artik holdover'a GIRERKEN
    # dondurulan FEE degeridir -- anlik FEE degil, cunku gecmiste
    # biriken hata sonradan degismez.
    state.holdover_started_at = datetime.now() - timedelta(hours=1)
    bir_saat_sonra = current_tint_seconds(state)
    assert bir_saat_sonra == pytest.approx(
        giris + state.holdover_entry_fee * 3600, rel=1e-3
    )

    # 5 saat geriye tarihle: 210 ns'lik saglik esigi (§3.6.18) asilmali
    state.holdover_started_at = datetime.now() - timedelta(hours=5)
    assert abs(current_tint_seconds(state)) > 210e-9


def test_noise_enabled_by_default():
    """
    Gurultu VARSAYILAN OLARAK ACIK olmali -- gercek cihaz davranisi
    budur. Sessizce kapali kalirsa simulator yine sabit deger
    dondurur ve FAZ 2'nin tum kazanimi kaybolur.
    """
    state = load_scenario("normal")
    assert state.noise_enabled is True
    assert state.noise_scale == 1.0


def test_noise_can_be_disabled_from_config():
    """
    Gurultuyu kapatabilmek gercek cihazla birebir cikti
    karsilastirmasi yaparken gerekli. Iki yol da calismali.
    """
    from gnsdo_simulator.config_loader import apply_config_to_state
    from gnsdo_simulator.device_state import DeviceState, measured_temperature

    kapali = DeviceState()
    apply_config_to_state(kapali, {"noise": {"enabled": False}})
    assert measured_temperature(kapali) == kapali.temperature_celsius

    sifir_olcek = DeviceState()
    apply_config_to_state(sifir_olcek, {"noise": {"scale": 0.0}})
    assert measured_temperature(sifir_olcek) == sifir_olcek.temperature_celsius


def test_noise_scale_reduces_amplitude():
    """
    Ara olcek degerleri genligi orantili azaltmali -- 0 ile 1
    arasinda kademeli gecis mumkun olsun.
    """
    from datetime import datetime, timedelta

    from gnsdo_simulator.config_loader import apply_config_to_state
    from gnsdo_simulator.device_state import DeviceState, measured_temperature

    an = datetime.now() - timedelta(seconds=137)

    tam = DeviceState(process_started_at=an)
    yari = DeviceState(process_started_at=an)
    apply_config_to_state(yari, {"noise": {"scale": 0.5}})

    taban = tam.temperature_celsius
    sapma_tam = abs(measured_temperature(tam) - taban)
    sapma_yari = abs(measured_temperature(yari) - taban)

    assert sapma_yari < sapma_tam


def test_tracking_cannot_exceed_visible():
    """
    TUTARLILIK KURALI: goremedigin bir uyduyu takip edemezsin.

    ILGINC NOT: gercek cihaz bu kurali her zaman tutmuyor -- kayitlarda
    GPS:SAT:TRAC:COUN? -> 20 iken GPS:SAT:VIS:COUN? -> 19 gorulmus.
    Iki sayac muhtemelen farkli seyleri sayiyor ve farkli anlarda
    ornekleniyor. Biz bu tuhafligi taklit etmiyoruz: simulatorun
    tutarli olmasi daha degerli (bkz. docs/tasarim-kararlari.md).
    """
    from gnsdo_simulator.config_loader import apply_config_to_state
    from gnsdo_simulator.device_state import DeviceState

    state = DeviceState()
    apply_config_to_state(state, {"gps": {"visible": 5, "tracking": 9}})

    assert state.gnss_satellites_tracking == 5
    assert state.gnss_satellites_visible == 5


def test_normal_scenario_satellite_counts_consistent():
    """Hazir senaryolarin hicbiri bu kurali ihlal etmemeli."""
    for senaryo in [
        "normal",
        "gnss-lost",
        "holdover",
        "warming-up",
        "not-locked",
        "hardware-error",
    ]:
        state = load_scenario(senaryo)
        assert (
            state.gnss_satellites_tracking <= state.gnss_satellites_visible
        ), f"{senaryo}: tracking > visible"
