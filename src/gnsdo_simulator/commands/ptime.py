"""
commands/ptime.py

Zaman/tarih komutlari: PTIME?, PTIME:DATE?, PTIME:TIME?, PTIME:TIME:STRING?,
ve gercek cihazin kilavuzunda PTIME?'in bileseni olarak tanimlanan
PTIME:TINT?, PTIME:OUTPUT?, PTIME:LEAP:ACC?.

ONEMLI GUNCELLEME: gercek cihazin kullanim kilavuzuna gore PTIME?
rastgele bir "tarih+saat" ozeti DEGIL -- TAM OLARAK su 5 sorgunun
sirayla birlestirilmis hali:
    PTIME:DATE?
    PTIME:TIME?
    PTIME:TINTerval?              (kilavuz: "SYNC:TINTerval? ile AYNI seydir")
    PTIME:OUTput?
    PTIME:LEAPsecond:ACCumulated?

Bu yuzden artik bu dosyadaki bazi fonksiyonlar da DeviceState'e
ihtiyac duyuyor (TINT, OUTPUT, LEAP:ACC icin) -- ama saf tarih/saat
komutlari (DATE?, TIME?, TIME:STRING?) hala sadece sistem saatine
bakiyor, state'e ihtiyac duymuyor.
"""

from datetime import datetime

from gnsdo_simulator.commands.sync import make_sync_tint_handler
from gnsdo_simulator.device_state import DeviceState
from gnsdo_simulator.scpi_parser import SCPIParser
from typing import Optional


def ptime_date_handler() -> str:
    """PTIME:DATE? -- sadece tarih, "YIL,AY,GUN"."""
    now = datetime.now()
    return now.strftime("%Y,%m,%d")


def ptime_time_handler() -> str:
    """
    PTIME:TIME? -- sadece saat, "SAAT,DAKIKA,SANIYE".
    Dokumandaki (gorev PDF'i) ornek: PTIME:TIME? -> 20,15,32
    """
    now = datetime.now()
    return now.strftime("%H,%M,%S")


def ptime_time_string_handler() -> str:
    """
    PTIME:TIME:STRING? -- okunabilir saat, "SAAT:DAKIKA:SANIYE".
    Dokumandaki ornek: PTIME:TIME:STRING? -> 20:15:32
    """
    now = datetime.now()
    return now.strftime("%H:%M:%S")


def make_ptime_output_query_handler(state: DeviceState):
    """
    PTIME:OUTPUT? -- iki cihazi seri kabloyla baglayip zaman
    bilgisi paylasma ozelligi acik mi ("ON"/"OFF").
    """

    def handler() -> str:
        return "ON" if state.ptime_output_enabled else "OFF"

    return handler


def make_ptime_output_setter(state: DeviceState):
    """PTIME:OUTPUT <ON|OFF> -- bu ozelligi acar/kapatir."""

    def setter(value: str) -> Optional[str]:
        state.ptime_output_enabled = value.strip().upper() == "ON"
        return None

    return setter


def make_ptime_leap_accumulated_handler(state: DeviceState):
    """PTIME:LEAP:ACC? -- GPS-UTC arasinda birikmis artik saniye sayisi."""

    def handler() -> str:
        return str(state.leap_second_accumulated)

    return handler


def make_ptime_handler(state: DeviceState, parser: SCPIParser):
    """
    PTIME? -- gercek cihazin kilavuzuna gore, asagidaki 5 sorgunun
    cevaplarini SIRAYLA birlestirir. Biz bunu, parser'da ZATEN
    kayitli olan handler'lari DOGRUDAN CAGIRARAK yapiyoruz -- boylece
    tek bir yerde (ornegin PTIME:TIME? formatinda) yapilacak bir
    degisiklik otomatik olarak PTIME?'e de yansir, iki yerde ayni
    mantigi tekrar yazmiyoruz.
    """

    def handler() -> str:
        lines = [
            parser.dispatch("PTIME:DATE?"),
            parser.dispatch("PTIME:TIME?"),
            parser.dispatch("PTIME:TINT?"),
            parser.dispatch("PTIME:OUTPUT?"),
            parser.dispatch("PTIME:LEAP:ACC?"),
        ]
        return "\r\n".join(line for line in lines if line is not None)

    return handler


def register_ptime_commands(parser: SCPIParser, state: DeviceState) -> None:
    """
    Bu dosyadaki tum PTIME komutlarini verilen parser'a kaydeder.

    NOT: artik "state" parametresi de aliyor -- TINT/OUTPUT/LEAP:ACC
    komutlari DeviceState'e ihtiyac duyuyor. Sadece DATE?/TIME?/
    TIME:STRING? hala saf sistem saatine bakiyor.
    """
    parser.register("PTIME:DATE?", ptime_date_handler)
    parser.register("PTIME:TIME?", ptime_time_handler)
    parser.register("PTIME:TIME:STRING?", ptime_time_string_handler)

    # PTIME:TINT? -- kilavuz bunun SYNC:TINTerval? ile AYNI oldugunu
    # soyluyor, o yuzden aynin fonksiyonu (make_sync_tint_handler)
    # tekrar kullaniyoruz -- iki ayri sabit degil, TEK bir kaynak.
    parser.register("PTIME:TINT?", make_sync_tint_handler(state))

    parser.register("PTIME:OUTPUT?", make_ptime_output_query_handler(state))
    parser.register_setter("PTIME:OUTPUT", make_ptime_output_setter(state))
    parser.register("PTIME:LEAP:ACC?", make_ptime_leap_accumulated_handler(state))

    # PTIME? en son kaydediliyor CUNKU yukaridaki komutlarin hepsinin
    # ONCE parser'a kayitli olmasi lazim (dispatch() ile onlari
    # cagirabilmesi icin).
    parser.register("PTIME?", make_ptime_handler(state, parser))

    # --- KISA/UZUN FORM ALIAS'LARI (gercek kilavuzdan) ---
    parser.register_alias("PTIME:TIME:STR?", "PTIME:TIME:STRING?")
    parser.register_alias("PTIME:TINTERVAL?", "PTIME:TINT?")
    parser.register_alias("PTIME:OUT?", "PTIME:OUTPUT?")
    parser.register_alias("PTIME:OUT", "PTIME:OUTPUT")
    parser.register_alias("PTIME:LEAPSECOND:ACCUMULATED?", "PTIME:LEAP:ACC?")