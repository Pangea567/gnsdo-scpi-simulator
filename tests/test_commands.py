"""
test_commands.py

Sistem komutlari (*IDN?, HELP?, SYST:STAT?) icin testler.

pytest calistirmak icin (repo kok dizininden):
    pytest tests/test_commands.py -v
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gnsdo_simulator.device_state import DeviceState
from gnsdo_simulator.scpi_parser import SCPIParser
from gnsdo_simulator.commands.system import register_system_commands


def make_test_parser() -> SCPIParser:
    """
    Her testte sifirdan, temiz bir parser + state kurmak icin
    kucuk bir yardimci fonksiyon. Boylece testler birbirini
    etkilemez (her biri kendi bagimsiz DeviceState'iyle calisir).
    """
    state = DeviceState()
    parser = SCPIParser()
    register_system_commands(parser, state)
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

    