"""
test_commands.py

Sistem komutlari (*IDN?, HELP?, SYST:STAT?) icin testler.

pytest calistirmak icin (repo kok dizininden):
    pytest tests/test_commands.py -v
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gnsdo_simulator.device_state import DeviceState
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
    register_ptime_commands(parser)
    register_sync_commands(parser, state)
    register_diagnostic_commands(parser)
    register_measure_commands(parser, state)
    register_csac_commands(parser, state)
    return parser


def test_idn():
    parser = make_test_parser()
    response = parser.dispatch("*IDN?")

    assert response is not None
    # Cevap virgulle ayrilmis 4 alan icermeli: Uretici, Model, SeriNo, Firmware
    parts = response.split(",")
    assert len(parts) == 4
    assert parts[0] == "Jackson Labs"
    assert parts[1] == "GNSDO"
    assert parts[2] == "SIM000001"
    assert parts[3] == "SIM-1.0"


def test_idn_uses_device_state():
    """
    *IDN? cevabinin gercekten DeviceState'ten okundugunu kanitlar --
    state'i degistirince cevabin da degismesi lazim.
    """
    state = DeviceState(serial_number="XYZ123", firmware_version="2.0")
    parser = SCPIParser()
    register_system_commands(parser, state)

    response = parser.dispatch("*IDN?")
    assert response == "Jackson Labs,GNSDO,XYZ123,2.0"


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

    # Varsayilan DeviceState: 8 uydu takip ediliyor (>= 4), yani kilitli olmali
    assert parser.dispatch("GPS?") == "LOCKED"
    assert parser.dispatch("GPS:SAT:TRAC:COUN?") == "8"
    assert parser.dispatch("GPS:SAT:VIS:COUN?") == "12"


def test_gps_no_fix_when_few_satellites():
    """
    GPS? cevabinin gercekten DeviceState'e bagli oldugunu kanitlar:
    takip edilen uydu sayisi esigin altina dusunce cevap degismeli.
    """
    state = DeviceState(gnss_satellites_tracking=2)
    parser = SCPIParser()
    register_system_commands(parser, state)
    register_gps_commands(parser, state)

    assert parser.dispatch("GPS?") == "NO FIX"


def test_syst_stat():
    parser = make_test_parser()
    response = parser.dispatch("SYST:STAT?")

    assert response == "OK"


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


def test_sync():
    parser = make_test_parser()

    # Varsayilan DeviceState: kilitli, holdover'da degil
    assert parser.dispatch("SYNC?") == "LOCKED"
    assert parser.dispatch("SYNC:LOCKED?") == "1"
    assert parser.dispatch("SYNC:HEALTH?") == "GOOD"
    # TINT icin tam degeri degil, bir sayi oldugunu kontrol edelim
    tint = parser.dispatch("SYNC:TINT?")
    assert tint is not None
    float(tint)  # sayiya cevrilebiliyor mu (hata firlatirsa test patlar)


def test_holdover_transition():
    """
    Dokumanin ozellikle istedigi test: SYNC:HOLD:INIT komutundan
    SONRA, SYNC:LOCKED?'in 0'a dusmesi ve SYNC:HOLD:DUR?'un artan
    bir sure dondurmesi gerekiyor.
    """
    parser = make_test_parser()

    # Once normal durumda kilitli olmali
    assert parser.dispatch("SYNC:LOCKED?") == "1"
    assert parser.dispatch("SYNC:HOLD:DUR?") == "0"

    # Holdover'i baslat
    response = parser.dispatch("SYNC:HOLD:INIT")
    assert response == ""  # setter, soylenecek bir sey yok ama cevap bos string (None degil)

    # Artik kilitli OLMAMALI
    assert parser.dispatch("SYNC:LOCKED?") == "0"
    assert parser.dispatch("SYNC?") == "HOLDOVER"

    # Bir sure gecmesini simule edip DUR?'un artip artmadigina bakalim
    time.sleep(0.2)
    dur = parser.dispatch("SYNC:HOLD:DUR?")
    assert dur is not None
    assert float(dur) > 0

    # Recovery baslatinca tekrar kilitli olmali
    parser.dispatch("SYNC:HOLD:REC:INIT")
    assert parser.dispatch("SYNC:LOCKED?") == "1"
    assert parser.dispatch("SYNC:HOLD:DUR?") == "0"


def test_sync_source_mode_setter():
    parser = make_test_parser()
    response = parser.dispatch("SYNC:SOUR:MODE EXTERNAL")
    assert response == ""  # cevap yok ama komut taninmis (None degil)


def test_diag():
    parser = make_test_parser()
    assert parser.dispatch("DIAG?") == "NO FAULT"


def test_measure():
    parser = make_test_parser()
    assert parser.dispatch("MEAS:TEMP?") == "42.5"
    assert parser.dispatch("MEAS:VOLT?") == "12.1"
    assert parser.dispatch("MEAS:CURR?") == "0.42"


def test_csac():
    parser = make_test_parser()
    assert parser.dispatch("CSAC:STATUS?") == "RUNNING"
    assert parser.dispatch("CSAC:SN?") == "CSAC-SIM-0001"