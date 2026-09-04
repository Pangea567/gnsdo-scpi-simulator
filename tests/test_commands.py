"""
test_commands.py

Sistem komutlari (*IDN?, HELP?, SYST:STAT?) icin testler.

pytest calistirmak icin (repo kok dizininden):
    pytest tests/test_commands.py -v
"""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gnsdo_simulator.device_state import DeviceState, is_locked
from gnsdo_simulator.scpi_parser import SCPIParser
from gnsdo_simulator.commands.system import register_system_commands
from gnsdo_simulator.commands.gps import register_gps_commands
from gnsdo_simulator.commands.ptime import register_ptime_commands
from gnsdo_simulator.commands.sync import register_sync_commands
from gnsdo_simulator.commands.diagnostic import register_diagnostic_commands
from gnsdo_simulator.commands.measure import register_measure_commands
from gnsdo_simulator.commands.csac import register_csac_commands


def make_test_parser() -> SCPIParser:
    """
    Her testte sifirdan, temiz bir parser + state kurmak icin
    kucuk bir yardimci fonksiyon. Boylece testler birbirini
    etkilemez (her biri kendi bagimsiz DeviceState'iyle calisir).

    Artik TUM komut gruplarini kaydediyoruz, boylece HELP? testi ve
    genel komut testleri gercek, tam bir simulator'i yansitiyor.
    """
    state = DeviceState()
    parser = SCPIParser()
    register_system_commands(parser, state)
    register_gps_commands(parser, state)
    register_ptime_commands(parser, state)
    register_sync_commands(parser, state)
    register_diagnostic_commands(parser, state)
    register_measure_commands(parser, state)
    register_csac_commands(parser, state)
    return parser


def test_idn():
    parser = make_test_parser()
    response = parser.dispatch("*IDN?")

    assert response is not None
    # GERCEK cihaz formati: "Jackson Labs, LN Rb GPSDO (PRE), Firmware Rev X.XX"
    # (seri numarasi burada YOK -- eski 4 alanli varsayimimiz yanlisti)
    assert response == "Jackson Labs, LN Rb GPSDO (PRE), Firmware Rev 1.17"


def test_idn_uses_device_state():
    """
    *IDN? cevabinin gercekten DeviceState'ten okundugunu kanitlar --
    state'i degistirince cevabin da degismesi lazim.
    """
    state = DeviceState(firmware_version="2.0")
    parser = SCPIParser()
    register_system_commands(parser, state)

    response = parser.dispatch("*IDN?")
    assert response == "Jackson Labs, LN Rb GPSDO (PRE), Firmware Rev 2.0"


def test_help():
    parser = make_test_parser()
    response = parser.dispatch("HELP?")

    assert response is not None
    assert "*IDN?" in response
    assert "SYST:STAT?" in response
    # Artik GPS komutlari da kayitli, HELP? bunlari da gostermeli
    # (elle guncellenen bir liste degil, parser'in gercek kayitlarindan
    # otomatik uretiliyor -- bunu kanitliyoruz)
    assert "GPS?" in response
    assert "GPS:SAT:TRAC:COUN?" in response


def test_gps():
    parser = make_test_parser()

    # Varsayilan DeviceState: 8 uydu takip ediliyor (>= 4), yani "3D Fix" olmali
    gps_response = parser.dispatch("GPS?")
    assert gps_response is not None
    lines = gps_response.split("\r\n")
    assert len(lines) == 22
    assert "GPS Receiver Status: 3D Fix" in lines
    assert "TRACKED SATS :8" in lines
    assert "VISIBLE SATS :12" in lines
    assert "N,4047.2368" in lines  # gercek konumdan donusturulmus enlem
    assert "HOLD POSITION:-267998828,-430158341,385929826" in lines

    assert parser.dispatch("GPS:SAT:TRAC:COUN?") == "8"
    assert parser.dispatch("GPS:SAT:VIS:COUN?") == "12"


def test_gps_no_fix_when_few_satellites():
    """
    GPS? cevabinin gercekten DeviceState'e bagli oldugunu kanitlar:
    takip edilen uydu sayisi esigin altina dusunce, konumla ilgili
    TUM alanlar (enlem/boylam/yukseklik/ECEF/sure/varyans) gercek
    cihazdaki gibi sifirlanmali/"gecersiz" degerlere donmeli.
    """
    state = DeviceState(gnss_satellites_tracking=2, gnss_satellites_visible=2)
    parser = SCPIParser()
    register_system_commands(parser, state)
    register_gps_commands(parser, state)

    gps_response = parser.dispatch("GPS?")
    assert gps_response is not None
    lines = gps_response.split("\r\n")
    assert "GPS Receiver Status: No Fix" in lines
    assert "N,   0.0000" in lines
    assert "E,   0.0000" in lines
    assert "0.00 m" in lines
    # Uydu sayilari GERCEK degerleri gostermeye devam etmeli (zorla 0 yapilmiyor)
    assert "TRACKED SATS :2" in lines
    assert "VISIBLE SATS :2" in lines
    # HOLD POSITION fix olsun olmasin AYNI kalmali (gercek cihazda oyleydi)
    assert "HOLD POSITION:-267998828,-430158341,385929826" in lines


def test_syst_stat():
    parser = make_test_parser()
    response = parser.dispatch("SYST:STAT?")

    assert response is not None
    lines = response.split("\r\n")
    assert lines[0].startswith("LN Rb GPSDO (PRE)")
    assert "Serial Number : 122301668" in lines[0]
    assert "Tracking:8        Not Tracking: 4" in lines
    assert "GPS Receiver Status: 3D Fix             GPSDO Status : Locked" in lines


def test_syst_stat_reflects_state():
    """
    SYST:STAT?'in "GPSDO Status" alaninin, state'e gore
    DEGISTIGINI kanitlar -- her farkli durumda dogru metni
    icermesi lazim (artik tek kelimelik cevap degil, tam bir
    rapor icinde bir alan).
    """
    from gnsdo_simulator.commands.system import register_system_commands

    # 1) Donanim arizasi -- en yuksek oncelikli, digerlerini gecersiz kilar
    state = DeviceState(hardware_fault=True)
    parser = SCPIParser()
    register_system_commands(parser, state)
    assert "GPSDO Status : Fault" in parser.dispatch("SYST:STAT?")

    # 2) Holdover
    state = DeviceState(holdover=True, sync_locked=False)
    parser = SCPIParser()
    register_system_commands(parser, state)
    assert "GPSDO Status : Holdover" in parser.dispatch("SYST:STAT?")

    # 3) warming-up senaryosu aktif (warmup_started_at dolu), henuz
    #    2 dakika gecmemis -> Warming Up
    state = DeviceState(sync_locked=False, warmup_started_at=datetime.now())
    parser = SCPIParser()
    register_system_commands(parser, state)
    assert "GPSDO Status : Warming Up" in parser.dispatch("SYST:STAT?")

    # 4) Uzun suredir calisiyor ama kilitlenememis (warmup_started_at
    #    YOK -- yani bu bir isinma degil, kalici bir sorun) -> Not Locked
    state = DeviceState(sync_locked=False)
    parser = SCPIParser()
    register_system_commands(parser, state)
    assert "GPSDO Status : Not Locked" in parser.dispatch("SYST:STAT?")


def test_locked_requires_fix():
    """
    YENI KURAL: GPS fix'i yoksa (yeterli uydu takip edilmiyorsa),
    is_locked() sync_locked ne olursa olsun False donmeli -- gercek
    dunyada osilator, GPS referansi olmadan kilitlenemez. Bu, daha
    once EKSIK olan bir tutarlilik kontrolu.
    """
    # sync_locked=True olsa BILE, fix yoksa (tracking < 4) kilitli SAYILMAMALI
    state = DeviceState(sync_locked=True, gnss_satellites_tracking=2)
    assert is_locked(state) is False

    # Yeterli uydu VARSA ve sync_locked=True ise, gercekten kilitli olmali
    state = DeviceState(sync_locked=True, gnss_satellites_tracking=8)
    assert is_locked(state) is True


def test_case_insensitive_command():
    parser = make_test_parser()

    assert parser.dispatch("*idn?") == parser.dispatch("*IDN?")
    assert parser.dispatch("help?") == parser.dispatch("HELP?")


def test_unknown_command():
    parser = make_test_parser()
    assert parser.dispatch("NOT:A:REAL:COMMAND?") is None


def test_ptime():
    """
    PTIME komutlari sistem saatinden geldigi icin sabit bir deger
    bekleyemeyiz -- onun yerine FORMATIN dogru oldugunu kontrol
    ediyoruz (ornegin PTIME:TIME? "SS,DD,SS" seklinde 3 sayidan
    olusmali).
    """
    parser = make_test_parser()

    time_response = parser.dispatch("PTIME:TIME?")
    assert time_response is not None
    parts = time_response.split(",")
    assert len(parts) == 3  # saat, dakika, saniye

    time_string_response = parser.dispatch("PTIME:TIME:STRING?")
    assert time_string_response is not None
    assert time_string_response.count(":") == 2  # "HH:MM:SS"

    date_response = parser.dispatch("PTIME:DATE?")
    assert date_response is not None
    assert len(date_response.split(",")) == 3  # yil, ay, gun

    # PTIME? artik gercek cihaz ciktisina gore ETIKETLI 5 satir:
    # "DATE :...", "TIME :...", "TINTerval :...", "OUTput :...",
    # "LEAPSECOND :..."
    ptime_response = parser.dispatch("PTIME?")
    assert ptime_response is not None
    lines = ptime_response.split("\r\n")
    assert len(lines) == 5
    assert lines[0].startswith("DATE :")
    assert lines[1].startswith("TIME :")
    assert lines[2].startswith("TINTerval :")
    assert lines[3] in ("OUTput :0", "OUTput :1")
    assert lines[4] == "LEAPSECOND :18"


def test_sync():
    parser = make_test_parser()

    # SYNC? artik gercek cihaz ciktisina gore ETIKETLI 12 satir
    sync_response = parser.dispatch("SYNC?")
    assert sync_response is not None
    lines = sync_response.split("\r\n")
    assert len(lines) == 12
    assert "1PPS LOCK STATUS  : 1" in lines  # varsayilan DeviceState: kilitli
    assert "HOLDOVER STATE: NONE" in lines
    assert any(line.startswith("HEALTH STATUS : 0x") for line in lines)

    assert parser.dispatch("SYNC:LOCKED?") == "1"

    # HEALTH? artik hex bit-mask -- "0x" ile baslamali, gecerli hex olmali
    health = parser.dispatch("SYNC:HEALTH?")
    assert health is not None
    assert health.startswith("0x")
    int(health, 16)  # gecerli bir hex sayi mi (hata firlatirsa test patlar)

    # TINT icin tam degeri degil, bir sayi oldugunu kontrol edelim
    tint = parser.dispatch("SYNC:TINT?")
    assert tint is not None
    float(tint)  # sayiya cevrilebiliyor mu (hata firlatirsa test patlar)


def test_holdover_transition():
    """
    Dokumanin ozellikle istedigi test: SYNC:HOLD:INIT komutundan
    SONRA, SYNC:LOCKED?'in 0'a dusmesi ve SYNC:HOLD:DUR?'un artan
    bir sure dondurmesi gerekiyor.

    NOT: SYNC:HOLD:DUR? gercek cihazda "sure,durum" seklinde IKI
    sayi doner (bkz. commands/sync.py), o yuzden burada virgulden
    once ve sonraki kismi ayri ayri kontrol ediyoruz.
    """
    parser = make_test_parser()

    # Once normal durumda kilitli olmali
    assert parser.dispatch("SYNC:LOCKED?") == "1"
    assert parser.dispatch("SYNC:HOLD:DUR?") == "0,0"

    # Holdover'i baslat
    response = parser.dispatch("SYNC:HOLD:INIT")
    assert response == ""  # setter, soylenecek bir sey yok ama cevap bos string (None degil)

    # Artik kilitli OLMAMALI
    assert parser.dispatch("SYNC:LOCKED?") == "0"
    sync_response = parser.dispatch("SYNC?")
    assert sync_response is not None
    assert "1PPS LOCK STATUS  : 0" in sync_response
    assert "HOLDOVER STATE: ACTIVE" in sync_response

    # Bir sure gecmesini simule edip DUR?'un artip artmadigina bakalim
    time.sleep(0.2)
    dur_response = parser.dispatch("SYNC:HOLD:DUR?")
    assert dur_response is not None
    duration_str, holdover_flag = dur_response.split(",")
    assert float(duration_str) > 0
    assert holdover_flag == "1"

    # Recovery baslatinca tekrar kilitli olmali
    parser.dispatch("SYNC:HOLD:REC:INIT")
    assert parser.dispatch("SYNC:LOCKED?") == "1"
    assert parser.dispatch("SYNC:HOLD:DUR?") == "0,0"


def test_sync_source_mode_setter():
    parser = make_test_parser()
    response = parser.dispatch("SYNC:SOUR:MODE EXTERNAL")
    assert response == ""  # cevap yok ama komut taninmis (None degil)


def test_diag():
    parser = make_test_parser()
    response = parser.dispatch("DIAG?")
    assert response is not None
    # ONEMLI: gercek cihaz ciktisinda "Fault:" satiri YOK -- artik
    # bu satiri beklemiyoruz.
    assert "Fault:" not in response
    assert "EFControl Relative: -0.410000%" in response
    assert "EFControl Absolute: -82.000000" in response
    assert "Lifetime : +871" in response


def test_measure():
    parser = make_test_parser()
    assert parser.dispatch("MEAS:TEMP?") == "42.5"
    assert parser.dispatch("MEAS:VOLT?") == "1.66"
    assert parser.dispatch("MEAS:CURR?") == "0.42"
    assert parser.dispatch("MEAS:POW?") == "11.7"

    # MEAS? artik gercek cihaz ciktisina gore ETIKETLI 4 satir,
    # CSAC Temperature dahil.
    meas_response = parser.dispatch("MEAS?")
    assert meas_response is not None
    assert meas_response.split("\r\n") == [
        "PCB Temperature: 42.5",
        "CSAC Temperature: 54.0",
        "TCXO Voltage: 1.66",
        "Power Supply Voltage: 11.7",
    ]


def test_csac():
    parser = make_test_parser()
    # Varsayilan DeviceState: sync_locked=True -> saglikli -> "0"
    # (GERCEK cihaz ciktisi ciplak sayi doner, hex degil)
    assert parser.dispatch("CSAC:STATUS?") == "0"
    assert parser.dispatch("CSAC:SN?") == "2209MX04906"

    # CSAC? artik gercek cihaz ciktisina gore ETIKETLI 13 satir
    csac_response = parser.dispatch("CSAC?")
    assert csac_response is not None
    lines = csac_response.split("\r\n")
    assert len(lines) == 13
    assert lines[0] == "RS232: OK"
    assert lines[2] == "STATUS: 0"
    assert lines[10] == "SN: 2209MX04906"
    assert lines[12].startswith("LIFETIME: ")

    # MAC? gercek cihazda CSAC? ile BIREBIR AYNI sonucu dondurmeli (alias)
    assert parser.dispatch("MAC?") == csac_response


def test_csac_status_reflects_lock_state():
    """CSAC:STATUS?'in gercekten kilit durumuna bagli oldugunu kanitlar."""
    from gnsdo_simulator.commands.csac import register_csac_commands

    state = DeviceState(sync_locked=False)
    parser = SCPIParser()
    register_csac_commands(parser, state)
    assert parser.dispatch("CSAC:STATUS?") == "1"