"""
commands/csac.py

CSAC (Chip Scale Atomic Clock -- cihazin icindeki kucuk Rubidium/
atomik saat modulu) komutlari.

GUNCELLEME (gercek cihazin GERCEK ciktisina gore):
  CSAC? artik SABIT alanlarla dolu, ETIKETLI 13 satirlik tam bir
  bilesim. Ayrica gercek cihaz ciktisinda "MAC?" diye AYRI bir komut
  daha var, ama cikan sonuc CSAC? ile BIREBIR AYNI -- yani bunlar
  ayni komutun iki farkli ismi (alias). register_alias() ile
  "MAC?"yi "CSAC?"e baglıyoruz.

  Standalone (tek basina) CSAC:STATUS? GERCEKTE ciplak bir sayi
  ("0"), bizim eski varsayimimiz (hex "0x0") YANLISTI -- duzelttik.
"""

from gnsdo_simulator.device_state import DeviceState, measured_csac_temperature, elapsed_hours_since_start, is_locked
from gnsdo_simulator.scpi_parser import SCPIParser


def make_csac_status_handler(state: DeviceState):
    """
    CSAC:STATUS? -- ONEMLI DUZELTME: gercek cihaz ciktisi CIPLAK bir
    sayi donuyor ("0"), bizim eski varsayimimiz ("0x0" gibi hex)
    YANLISTI -- kilavuzun anlattigi hex bit-mask ile GERCEK ciktinin
    formati uyusmuyormus, biz GERCEK ciktiyi esas aliyoruz.
    is_locked()'a bagliyoruz (warming-up senaryosunda gercek 2
    dakikalik sure gecince otomatik "0" olur).
    """

    def handler() -> str:
        return "0" if is_locked(state) else "1"

    return handler


def make_csac_temp_handler(state: DeviceState):
    def handler() -> str:
        return f"{measured_csac_temperature(state):.2f}"

    return handler


def make_csac_sn_handler(state: DeviceState):
    def handler() -> str:
        return state.csac_serial_number

    return handler


def make_csac_lifetime_handler(state: DeviceState):
    """
    CSAC:LIFEtime? -- DIAG?'in Lifetime'i gibi, bu da GERCEKTEN
    zamanla artiyor (baslangic degeri + simulator'in calisma suresi).
    """

    def handler() -> str:
        return str(state.csac_lifetime_base_hours + int(elapsed_hours_since_start(state)))

    return handler


def make_csac_handler(state: DeviceState):
    """
    CSAC? -- gercek cihaz ciktisina gore ETIKETLI 13 satir:

        RS232: OK
        STEER: -71.000
        STATUS: 0
        MODE: 0x0000
        TEC CONTROL: 56.22
        DDS CENTER: 0.00
        TCXO VOLTAGE: 1.658
        DC SIGNAL LEVEL: 1.00
        HEAT PACKAGE: 2730.00
        TEMPERATURE: 54.36
        SN: 2209MX04906
        FIRMWARE REV: V1.0.23
        LIFETIME: 11247

    NOT: "TCXO VOLTAGE" burada, MEAS:VOLT?'taki ile AYNI state
    alanini (state.voltage) kullaniyor -- gercek cihazda da muhtemelen
    ayni fiziksel olcumun iki farkli yerden okunmus hali, biz de
    TEK bir kaynaktan (tutarlilik icin) okuyoruz.
    """

    def handler() -> str:
        status = "0" if is_locked(state) else "1"
        lifetime = state.csac_lifetime_base_hours + int(elapsed_hours_since_start(state))

        lines = [
            f"RS232: {state.csac_rs232_status}",
            f"STEER: {state.csac_steer:.3f}",
            f"STATUS: {status}",
            f"MODE: {state.csac_mode}",
            f"TEC CONTROL: {state.csac_tec_control:.2f}",
            f"DDS CENTER: {state.csac_dds_center:.2f}",
            f"TCXO VOLTAGE: {state.voltage:.3f}",
            f"DC SIGNAL LEVEL: {state.csac_dc_signal_level:.2f}",
            f"HEAT PACKAGE: {state.csac_heat_package:.2f}",
            f"TEMPERATURE: {measured_csac_temperature(state):.2f}",
            f"SN: {state.csac_serial_number}",
            f"FIRMWARE REV: {state.csac_firmware_rev}",
            f"LIFETIME: {lifetime}",
        ]
        return "\r\n".join(lines)

    return handler


def register_csac_commands(parser: SCPIParser, state: DeviceState) -> None:
    parser.register("CSAC:STATUS?", make_csac_status_handler(state))
    parser.register("CSAC:TEMP?", make_csac_temp_handler(state))
    parser.register("CSAC:SN?", make_csac_sn_handler(state))
    parser.register("CSAC:LIFE?", make_csac_lifetime_handler(state))
    parser.register("CSAC?", make_csac_handler(state))

    # --- KISA/UZUN FORM VE ALIAS'LAR ---
    # Kilavuz: "CSAC:STATus?" -> mandatory kisa form "CSAC:STAT?"
    # (bizim canonical'imiz "STATUS" -- gorev PDF'i oyle istemisti).
    parser.register_alias("CSAC:STAT?", "CSAC:STATUS?")
    parser.register_alias("CSAC:LIFETIME?", "CSAC:LIFE?")

    # GERCEK cihaz ciktisinda "MAC?" diye ayri bir komut var ama
    # sonucu CSAC? ile BIREBIR AYNI -- alias olarak ekliyoruz.
    parser.register_alias("MAC?", "CSAC?")