"""
commands/csac.py

CSAC (Chip Scale Atomic Clock -- cihazin icindeki kucuk Rubidium/
atomik saat modulu) komutlari: CSAC?, CSAC:STATUS?, CSAC:TEMP?, CSAC:SN?

GUNCELLEME (gercek cihazin kilavuzuna gore):
  - CSAC:STATUS? bizim eski varsayimimiz gibi "RUNNING" METNI DEGIL,
    HEX bir deger: 0x0 = kilitli ve saglikli, 0x1 = kilitli degil.
    Bu, DeviceState'teki genel kilit durumuna (sync_locked) bagliyoruz
    -- CSAC/Rubidium'un kilitlenmesi, cihazin genel senkron kilidiyle
    dogrudan iliskili oldugu icin bu makul bir baglanti.
  - CSAC:SN? gercek formati "YYMMCSNNNNN" (uretim yili+ayi + "CS" +
    o ayin seri sirasi) -- eski "CSAC-SIM-0001" degerimiz bu kaliba
    uymuyordu, duzelttik (bkz. device_state.py).
"""

from gnsdo_simulator.device_state import DeviceState, is_locked
from gnsdo_simulator.scpi_parser import SCPIParser


def make_csac_status_handler(state: DeviceState):
    """
    CSAC:STATUS? -- gercek kilavuza gore hex: 0x1 = kilitli degil,
    0x0 = kilitli ve saglikli. is_locked()'a bagliyoruz (warming-up
    senaryosunda gercek 2 dakikalik sure gecince otomatik "0x0" olur).
    """

    def handler() -> str:
        return "0x0" if is_locked(state) else "0x1"

    return handler


def make_csac_temp_handler(state: DeviceState):
    def handler() -> str:
        return str(state.csac_temperature_celsius)

    return handler


def make_csac_sn_handler(state: DeviceState):
    def handler() -> str:
        return state.csac_serial_number

    return handler


def make_csac_handler(state: DeviceState, parser: SCPIParser):
    """
    CSAC? -- kilavuz "yukaridaki tum CSAC sorgularini gosterir" diyor.
    Biz su an implemente ettigimiz uc alt sorguyu (STATUS?, TEMP?, SN?)
    birlestiriyoruz -- kilavuzdaki tam liste daha uzun (RS232?, STeer?,
    MODE?, TECcontrol?, TCXO?, SIGnal?, HEATpackage?, FWrev?, LIFEtime?
    de var), bunlari henuz simule etmiyoruz (backlog).
    """

    def handler() -> str:
        lines = [
            parser.dispatch("CSAC:STATUS?"),
            parser.dispatch("CSAC:TEMP?"),
            parser.dispatch("CSAC:SN?"),
        ]
        return "\r\n".join(line for line in lines if line is not None)

    return handler


def register_csac_commands(parser: SCPIParser, state: DeviceState) -> None:
    parser.register("CSAC:STATUS?", make_csac_status_handler(state))
    parser.register("CSAC:TEMP?", make_csac_temp_handler(state))
    parser.register("CSAC:SN?", make_csac_sn_handler(state))
    parser.register("CSAC?", make_csac_handler(state, parser))

    # Kilavuz: "CSAC:STATus?" -> mandatory kisa form "CSAC:STAT?"
    # (bizim canonical'imiz "STATUS" -- gorev PDF'i oyle istemisti).
    parser.register_alias("CSAC:STAT?", "CSAC:STATUS?")