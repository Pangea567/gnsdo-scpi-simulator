"""
commands/measure.py

Olcum komutlari: MEAS?, MEAS:TEMP?, MEAS:VOLT?, MEAS:CURR?

Ayni "make_X_handler(state)" deseni: cevaplar DeviceState'ten
okunuyor. Gercekci bir sensor gurultusu/degisimi simule etmiyoruz
(proje kararimiz geregi), sabit degerler donuyoruz -- DeviceState
uzerinden, koda gomulu (hardcoded) degil.
"""

from gnsdo_simulator.device_state import DeviceState
from gnsdo_simulator.scpi_parser import SCPIParser


def make_meas_handler(state: DeviceState):
    """MEAS? -- genel olcum ozeti, virgulle ayrilmis: sicaklik,voltaj,akim."""

    def handler() -> str:
        return f"{state.temperature_celsius},{state.voltage},{state.current}"

    return handler


def make_meas_temp_handler(state: DeviceState):
    def handler() -> str:
        return str(state.temperature_celsius)

    return handler


def make_meas_volt_handler(state: DeviceState):
    def handler() -> str:
        return str(state.voltage)

    return handler


def make_meas_curr_handler(state: DeviceState):
    def handler() -> str:
        return str(state.current)

    return handler


def register_measure_commands(parser: SCPIParser, state: DeviceState) -> None:
    parser.register("MEAS?", make_meas_handler(state))
    parser.register("MEAS:TEMP?", make_meas_temp_handler(state))
    parser.register("MEAS:VOLT?", make_meas_volt_handler(state))
    parser.register("MEAS:CURR?", make_meas_curr_handler(state))