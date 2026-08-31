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
    GPS? komutu: GNSS alicisinin GENEL, ZENGIN durum ozeti.

    NOT: gercek cihazin kullanim kilavuzunda bu komutun aciklamasi
    soyleydi: "konfigurasyon, konum, hiz, yukseklik ve diger ilgili
    verileri tek yerde gosterir" -- ama TAM ornek cikti bulunamadi.
    Bu yuzden, DIAG?'ta oldugu gibi COK SATIRLI bir cevap kurguluyoruz,
    aciklamada gecen alanlarin hepsini iceriyor. Bu bizim MAKUL bir
    varsayimimiz -- gercek cihazin birebir ayni format kullandigini
    iddia etmiyoruz. Gercek ornek cikti bulunursa, sadece bu
    fonksiyonun icindeki formatlama degisecek.
    """

    def gps_handler() -> str:
        fix = "3D FIX" if state.gnss_satellites_tracking >= MIN_SATELLITES_FOR_LOCK else "NO FIX"
        lines = [
            f"Fix: {fix}",
            f"Satellites Tracking: {state.gnss_satellites_tracking}",
            f"Satellites Visible: {state.gnss_satellites_visible}",
            f"Latitude: {state.gps_latitude}",
            f"Longitude: {state.gps_longitude}",
            f"Altitude: {state.gps_altitude_m} m",
            f"Speed: {state.gps_speed_kmh} km/h",
        ]
        return "\r\n".join(lines)

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