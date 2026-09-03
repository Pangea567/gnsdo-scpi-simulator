"""
commands/measure.py

Olcum komutlari: MEAS?, MEAS:TEMP?, MEAS:VOLT?, MEAS:CURR?, MEAS:POW?

GUNCELLEME (gercek cihazin GERCEK ciktisina gore):
  - Standalone MEAS:TEMP?/VOLT?/CURR?/POW? ciplak (etiketsiz) sayi
    donuyor -- bu zaten dogruydu, degismedi.
  - MEAS? (tum olcumleri birden gosteren komut) ETIKETLI 4 satir
    donuyor, VE bizim eskiden hic dahil etmedigimiz "CSAC Temperature"
    satirini da iceriyor:

        PCB Temperature: 46.5688
        CSAC Temperature: 47.83
        TCXO Voltage: 1.672
        Power Supply Voltage: 11.71

  - MEAS:VOLT? gercekte TCXO ayar voltaji (kucuk, ~1.6-1.7V) --
    guc kaynagi voltaji DEGIL (o MEAS:POW?).
  - MEAS:CURR? gercek ciktida "51.3210" gibi bir deger donuyor --
    PCB sicakligiyla ayni olcekte, yani gercekten "akim" degil,
    kilavuzun da dedigi gibi legacy/farkli bir olcum. Biz yine de
    ayri "current" alanini kullanmaya devam ediyoruz (deger anlami
    degisse de format/davranis etkilenmiyor).
"""

from gnsdo_simulator.device_state import DeviceState
from gnsdo_simulator.scpi_parser import SCPIParser


def make_meas_temp_handler(state: DeviceState):
    """MEAS:TEMP? -- PCB sicakligi. Ciplak sayi doner (etiketsiz)."""

    def handler() -> str:
        return str(state.temperature_celsius)

    return handler


def make_meas_volt_handler(state: DeviceState):
    """MEAS:VOLT? -- TCXO ayar voltaji. Ciplak sayi doner (etiketsiz)."""

    def handler() -> str:
        return str(state.voltage)

    return handler


def make_meas_curr_handler(state: DeviceState):
    """MEAS:CURR? -- legacy olcum (gercekte akim degil). Ciplak sayi doner."""

    def handler() -> str:
        return str(state.current)

    return handler


def make_meas_powersupply_handler(state: DeviceState):
    """MEAS:POW? -- guc kaynagi giris voltaji. Ciplak sayi doner."""

    def handler() -> str:
        return str(state.power_supply_voltage)

    return handler


def make_meas_handler(state: DeviceState):
    """
    MEAS? -- gercek cihaz ciktisina gore ETIKETLI 4 satir. Dikkat:
    "CSAC Temperature" satiri, standalone bir "MEAS:CSAC:TEMP?"
    komutu olarak AYRICA sorulamiyor -- SADECE bu bilesimin icinde
    goruluyor. Biz zaten var olan csac_temperature_celsius alanini
    burada tekrar kullaniyoruz (CSAC komutlarindaki ile ayni deger).
    """

    def handler() -> str:
        lines = [
            f"PCB Temperature: {state.temperature_celsius}",
            f"CSAC Temperature: {state.csac_temperature_celsius}",
            f"TCXO Voltage: {state.voltage}",
            f"Power Supply Voltage: {state.power_supply_voltage}",
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