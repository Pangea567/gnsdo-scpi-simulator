"""
test_parser.py

SCPIParser icin temel testler.

pytest calistirmak icin (repo kok dizininden):
    pytest tests/test_parser.py -v
"""

import sys
import os

# src/ klasorunu Python'un modul arama yoluna ekliyoruz ki
# "from gnsdo_simulator.scpi_parser import ..." calissin.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gnsdo_simulator.scpi_parser import SCPIParser, normalize_command


def test_normalize_command_handles_crlf():
    assert normalize_command(b"*IDN?\r\n") == "*IDN?"
    assert normalize_command(b"*IDN?\n") == "*IDN?"
    assert normalize_command(b"*IDN?\r") == "*IDN?"


def test_normalize_command_strips_whitespace():
    assert normalize_command("   MEAS:TEMP?   ") == "MEAS:TEMP?"


def test_case_insensitive_command():
    parser = SCPIParser()
    parser.register("*IDN?", lambda: "Jackson Labs,GNSDO,SIM000001,SIM-1.0")

    # Kucuk harfle, buyuk harfle, karisik harfle hepsi ayni sonucu vermeli
    assert parser.dispatch("*idn?") == "Jackson Labs,GNSDO,SIM000001,SIM-1.0"
    assert parser.dispatch("*IDN?") == "Jackson Labs,GNSDO,SIM000001,SIM-1.0"
    assert parser.dispatch("*IdN?") == "Jackson Labs,GNSDO,SIM000001,SIM-1.0"


def test_unknown_command_does_not_crash():
    parser = SCPIParser()
    parser.register("*IDN?", lambda: "some response")

    # Kayitli olmayan bir komut gonderiyoruz. Exception FIRLAMAMALI.
    result = parser.dispatch("FOO:BAR:BAZ?")
    assert result is None


def test_dispatch_with_raw_bytes():
    parser = SCPIParser()
    parser.register("SYNC:LOCKED?", lambda: "1")

    result = parser.dispatch(b"SYNC:LOCKED?\r\n")
    assert result == "1"


def test_empty_line_returns_none():
    parser = SCPIParser()
    parser.register("*IDN?", lambda: "some response")

    assert parser.dispatch(b"\r\n") is None
    assert parser.dispatch("") is None


def test_alias_resolves_to_canonical_query():
    """
    register_alias() ile kaydedilen bir "uzun form", GERCEKTEN
    kayitli "kisa/asil" (canonical) komutla ayni cevabi vermeli --
    kisa ve uzun SCPI komut bicimi destegini kanitlar.
    """
    parser = SCPIParser()
    parser.register("SYNC:HEA?", lambda: "0x0")
    parser.register_alias("SYNCHRONIZATION:HEALTH?", "SYNC:HEA?")

    assert parser.dispatch("SYNC:HEA?") == "0x0"
    assert parser.dispatch("SYNCHRONIZATION:HEALTH?") == "0x0"
    # Case-insensitive de calismali
    assert parser.dispatch("synchronization:health?") == "0x0"


def test_alias_resolves_to_canonical_setter():
    """Alias mekanizmasi setter (deger alan) komutlarda da calismali."""
    received = {}

    def setter(value):
        received["value"] = value
        return None

    parser = SCPIParser()
    parser.register_setter("SYNC:SOUR:MODE", setter)
    parser.register_alias("SYNCHRONIZATION:SOURCE:MODE", "SYNC:SOUR:MODE")

    parser.dispatch("SYNCHRONIZATION:SOURCE:MODE GPS")
    assert received["value"] == "GPS"


def test_unknown_alias_returns_none():
    """Kayitli olmayan bir alias, bilinmeyen komut gibi None donmeli."""
    parser = SCPIParser()
    parser.register("*IDN?", lambda: "x")
    assert parser.dispatch("BOYLE:BIR:UZUN:KOMUT:YOK?") is None