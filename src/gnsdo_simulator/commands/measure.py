"""
commands/measure.py

Olcum komutlari: MEAS?, MEAS:TEMP?, MEAS:VOLT?, MEAS:CURR?, MEAS:POW?

GUNCELLEME (gercek cihazin kilavuzuna gore):
  - MEAS? gercekte 4 sorgunun bilesimi: TEMP?, VOLT?, CURR?, POWersupply?
    (biz eskiden sadece ilk 3'unu kullaniyorduk, POWersupply? EKSIKTI).
  - MEAS:VOLT? gercekte "guc kaynagi voltaji" DEGIL, TCXO ayar voltaji.
  - MEAS:CURR? gercekte "akim" degil (isim yaniltici/legacy) -- gercek
    cihazda Rubidium ic sicakligi ya da filtre osilator PCB sicakligi
    donuyor. Biz yine de mevcut "current" alanini kullanmaya devam
    ediyoruz (deger anlami degisse de sayisal formati etkilemiyor),
    ama bunu yorumda belirtiyoruz ki yanlis anlasilmasin.
  - MEAS:POW? (POWersupply?) gercek guc kaynagi giris voltaji -- bu
    YENI eklendi (state.power_supply_voltage).
"""

from gnsdo_simulator.device_state import DeviceState
from gnsdo_simulator.scpi_parser import SCPIParser


def make_meas_temp_handler(state: DeviceState):
    """MEAS:TEMP? -- Rubidium/filtre osilator civarindaki PCB sicakligi."""

    def handler() -> str:
        return str(state.temperature_celsius)

    return handler


def make_meas_volt_handler(state: DeviceState):
    """MEAS:VOLT? -- TCXO ayar voltaji (guc kaynagi voltaji DEGIL)."""

    def handler() -> str:
        return str(state.voltage)

    return handler


def make_meas_curr_handler(state: DeviceState):
    """
    MEAS:CURR? -- Legacy SCPI komutu. Gercek cihazda isminin aksine
    akim degil, ic Rubidium sicakligi ya da filtre PCB sicakligi
    donuyor. Biz mevcut "current" alanini kullanmaya devam ediyoruz.
    """

    def handler() -> str:
        return str(state.current)

    return handler


def make_meas_powersupply_handler(state: DeviceState):
    """MEAS:POW? (POWersupply?) -- guc kaynagi giris voltaji."""

    def handler() -> str:
        return str(state.power_supply_voltage)

    return handler


def make_meas_handler(state: DeviceState):
    """
    MEAS? -- gercek cihazin kilavuzuna gore TAM OLARAK su 4 sorgunun
    sirayla birlestirilmis hali: TEMP?, VOLT?, CURR?, POWersupply?
    """

    def handler() -> str:
        lines = [
            str(state.temperature_celsius),
            str(state.voltage),
            str(state.current),
            str(state.power_supply_voltage),
        ]
        return "\r\n".join(lines)

    return handler


def register_measure_commands(parser: SCPIParser, state: DeviceState) -> None:
    parser.register("MEAS?", make_meas_handler(state))
    parser.register("MEAS:TEMP?", make_meas_temp_handler(state))
    parser.register("MEAS:VOLT?", make_meas_volt_handler(state))
    parser.register("MEAS:CURR?", make_meas_curr_handler(state))
    parser.register("MEAS:POW?", make_meas_powersupply_handler(state))

    # --- KISA/UZUN FORM ALIAS'LARI (gercek kilavuzdan) ---
    parser.register_alias("MEASURE?", "MEAS?")
    parser.register_alias("MEASURE:TEMPERATURE?", "MEAS:TEMP?")
    parser.register_alias("MEASURE:VOLTAGE?", "MEAS:VOLT?")
    parser.register_alias("MEASURE:CURRENT?", "MEAS:CURR?")
    parser.register_alias("MEASURE:POWERSUPPLY?", "MEAS:POW?")