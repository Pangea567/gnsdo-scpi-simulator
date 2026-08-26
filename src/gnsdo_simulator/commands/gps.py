"""
commands/gps.py

GPS/GNSS ile ilgili komutlar: GPS?, GPS:SAT:TRAC:COUN?, GPS:SAT:VIS:COUN?

Ayni "make_X_handler(state) -> fonksiyon" deseni burada da devam
ediyor (bkz. commands/system.py'deki make_idn_handler acıklamasi):
cevaplarimiz DeviceState'e bagli oldugu icin, state'i "hatirlayan"
kucuk fonksiyonlar uretiyoruz.
"""

from gnsdo_simulator.device_state import DeviceState
from gnsdo_simulator.scpi_parser import SCPIParser


# Gercek GPS alicilarinin konum hesaplayabilmesi icin genelde en az
# 4 uyduyu ES ZAMANLI takip etmesi (tracking) gerekir. Karmasik bir
# GPS/yakinsama algoritmasi yazmiyoruz -- sadece bu bilinen, basit
# esik degerini kullanarak "kilitli mi degil mi" karari veriyoruz.
MIN_SATELLITES_FOR_LOCK = 4


def make_gps_handler(state: DeviceState):
    """
    GPS? komutu: GPS alicisinin genel durumunu doner.

    Basit kural: takip edilen uydu sayisi esik degerin (4) uzerinde
    ya da esitse "LOCKED", degilse "NO FIX" doneriz. Bu deger
    DeviceState'ten okundugu icin, ileride "gnss-lost" senaryosunu
    ekledigimizde (tracking sayisini 0'a cektigimizde), GPS? cevabi
    otomatik olarak "NO FIX"a donecek -- GPS? fonksiyonuna hic
    dokunmamiza gerek kalmayacak.
    """

    def gps_handler() -> str:
        if state.gnss_satellites_tracking >= MIN_SATELLITES_FOR_LOCK:
            return "LOCKED"
        return "NO FIX"

    return gps_handler


def make_gps_sat_tracking_handler(state: DeviceState):
    """GPS:SAT:TRAC:COUN? -- kac uydu su an takip ediliyor (tracking)."""

    def handler() -> str:
        return str(state.gnss_satellites_tracking)

    return handler


def make_gps_sat_visible_handler(state: DeviceState):
    """GPS:SAT:VIS:COUN? -- ufukta kac uydu gorunuyor (visible)."""

    def handler() -> str:
        return str(state.gnss_satellites_visible)

    return handler


def register_gps_commands(parser: SCPIParser, state: DeviceState) -> None:
    """Bu dosyadaki tum GPS komutlarini verilen parser'a kaydeder."""
    parser.register("GPS?", make_gps_handler(state))
    parser.register("GPS:SAT:TRAC:COUN?", make_gps_sat_tracking_handler(state))
    parser.register("GPS:SAT:VIS:COUN?", make_gps_sat_visible_handler(state))
    