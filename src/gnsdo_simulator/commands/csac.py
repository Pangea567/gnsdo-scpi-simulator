"""
commands/csac.py

CSAC (Chip Scale Atomic Clock) komutlari: CSAC?, CSAC:STATUS?,
CSAC:TEMP?, CSAC:SN?

CSAC, cihazin icindeki kucuk atomik saat modulu -- ayri bir
"alt cihaz" gibi dusunulebilir, kendi durumu/sicakligi/seri
numarasi var. Ayni desen: DeviceState'ten okuyan basit fonksiyonlar.
"""

from gnsdo_simulator.device_state import DeviceState
from gnsdo_simulator.scpi_parser import SCPIParser


def make_csac_handler(state: DeviceState):
    """CSAC? -- genel CSAC ozeti (durum,sicaklik)."""

    def handler() -> str:
        return f"{state.csac_status},{state.csac_temperature_celsius}"

    return handler


def make_csac_status_handler(state: DeviceState):
    def handler() -> str:
        return state.csac_status

    return handler


def make_csac_temp_handler(state: DeviceState):
    def handler() -> str:
        return str(state.csac_temperature_celsius)

    return handler


def make_csac_sn_handler(state: DeviceState):
    def handler() -> str:
        return state.csac_serial_number

    return handler


def register_csac_commands(parser: SCPIParser, state: DeviceState) -> None:
    parser.register("CSAC?", make_csac_handler(state))
    parser.register("CSAC:STATUS?", make_csac_status_handler(state))
    parser.register("CSAC:TEMP?", make_csac_temp_handler(state))
    parser.register("CSAC:SN?", make_csac_sn_handler(state))