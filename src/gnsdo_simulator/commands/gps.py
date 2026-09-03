"""
commands/gps.py

GPS/GNSS ile ilgili komutlar: GPS?, GPS:SAT:TRAC:COUN?, GPS:SAT:VIS:COUN?

GUNCELLEME (gercek cihazin GERCEK ciktisina gore):
  GPS? artik gercek cihaz gibi 22 satirlik, NMEA tarzi bir rapor.
  Kullanicinin PAYLASTIGI iki gercek ornekten (biri sinyal VARKEN,
  biri anten SOKULMUSKEN/sinyal YOKKEN) ogrendik ki konumla ilgili
  alanlar (enlem/boylam/yukseklik/hiz/ECEF/sure/varyans) fix
  olmayinca SIFIRLANIYOR, ama uydu sayilari ve diger sabit ayarlar
  (survey limitleri, hold position, timing mode...) DEGISMIYOR.
"""

from gnsdo_simulator.device_state import DeviceState
from gnsdo_simulator.scpi_parser import SCPIParser


# Gercek GPS alicilarinin konum hesaplayabilmesi icin genelde en az
# 4 uyduyu ES ZAMANLI takip etmesi (tracking) gerekir. Karmasik bir
# GPS/yakinsama algoritmasi yazmiyoruz -- sadece bu bilinen, basit
# esik degerini kullanarak "fix var mi yok mu" karari veriyoruz.
MIN_SATELLITES_FOR_LOCK = 4

# Fix yokken gercek cihaz ciktisinda gorulen sabit degerler (kullanicinin
# "anten sokulmus" ornek ciktisindan alindi).
NO_FIX_SURVEY_DURATION = 14
NO_FIX_3D_VARIANCE = 4294967295  # 32-bit "gecersiz/sonsuz" sentinel degeri


def _to_ddmm(value: float) -> str:
    """
    Ondalik dereceyi ("40.78728" gibi) NMEA tarzi "DDMM.MMMM" metnine
    cevirir ("4047.2368" gibi) -- derece kismini oldugu gibi, dakika
    kismini 2 basamak + 4 ondalik olarak yaziyoruz.
    """
    degrees = int(abs(value))
    minutes = (abs(value) - degrees) * 60
    return f"{degrees}{minutes:07.4f}"


def make_gps_handler(state: DeviceState):
    """
    GPS? -- gercek cihaz ciktisina gore ETIKETLI 22 satir.
    Konumla ilgili alanlar SADECE fix varken (tracked >= esik)
    gercek degerleri gosterir; fix yokken hepsi sifirlanir/sabit
    "yok" degerlerine doner -- tipki gercek cihazda oldugu gibi.
    """

    def handler() -> str:
        has_fix = state.gnss_satellites_tracking >= MIN_SATELLITES_FOR_LOCK

        if has_fix:
            lat_str = _to_ddmm(state.gps_latitude).rjust(9)
            lon_str = _to_ddmm(state.gps_longitude).rjust(9)
            height = f"{state.gps_altitude_m:.2f} m"
            speed = f"{state.gps_speed_knots:.2f} Knots"
            heading = f"{state.gps_heading_degrees:.2f} Degrees"
            fix_status = "3D Fix"
            pulse_sawtooth = state.gps_pulse_sawtooth
            duration = state.gps_survey_duration_seconds
            ecef = f"{state.gps_ecef_x},{state.gps_ecef_y},{state.gps_ecef_z}"
            variance = state.gps_3d_variance
        else:
            lat_str = "0.0000".rjust(9)
            lon_str = "0.0000".rjust(9)
            height = "0.00 m"
            speed = "0.00 Knots"
            heading = "0.00 Degrees"
            fix_status = "No Fix"
            pulse_sawtooth = 0.0
            duration = NO_FIX_SURVEY_DURATION
            ecef = "0,0,0"
            variance = NO_FIX_3D_VARIANCE

        lines = [
            f"GNSS: {state.gnss_constellations} ",
            f"ANTENNA DELAY:{state.gps_antenna_delay_seconds}",
            f"PULSE SAWTOOTH:{pulse_sawtooth}",
            f"TRACKED SATS :{state.gnss_satellites_tracking}",
            f"VISIBLE SATS :{state.gnss_satellites_visible}",
            "ACTUAL POSITION:",
            f"N,{lat_str}",
            f"E,{lon_str}",
            height,
            speed,
            heading,
            f"GPS Receiver Status: {fix_status}",
            f"DYNAMIC MODE:{state.gps_dynamic_mode_label}",
            f"DYNAMIC STATE:{state.gps_dynamic_state_label}",
            f"SURVEY MIN DURATION:{state.gps_survey_min_duration}",
            f"SURVEY VARIANCE LIMIT:{state.gps_survey_variance_limit}",
            f"SURVEY STATUS:{state.gps_survey_status}",
            f"Duration : {duration}, ECEF {ecef}, 3D variance {variance}",
            f"TIMING MODE:{state.gps_timing_mode}",
            f"HOLD POSITION:{state.gps_hold_position}",
            f"JAMMING LEVEL:{state.gps_jamming_level}",
            f"FIRMWARE VERSION: {state.gps_firmware_version}",
        ]
        return "\r\n".join(lines)

    return handler


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

    # --- KISA/UZUN FORM ALIAS'LARI (gercek kilavuzdan) ---
    parser.register_alias("GPS:SAT:TRA:COUN?", "GPS:SAT:TRAC:COUN?")
    parser.register_alias("GPS:SATELLITE:TRACKING:COUNT?", "GPS:SAT:TRAC:COUN?")
    parser.register_alias("GPS:SATELLITE:VISIBLE:COUNT?", "GPS:SAT:VIS:COUN?")