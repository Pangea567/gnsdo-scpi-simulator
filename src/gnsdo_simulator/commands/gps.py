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

from gnsdo_simulator.device_state import DeviceState, MIN_SATELLITES_FOR_LOCK
from gnsdo_simulator.scpi_parser import SCPIParser


# NOT: MIN_SATELLITES_FOR_LOCK artik device_state.py'de tanimli --
# cunku hem GPS?'in "fix var mi" hesabi hem de is_locked()'in "fix
# olmadan kilitlenemez" kontrolu AYNI esik degerini paylasmali.
# Burada tekrar tanimlamak yerine oradan iceri aktariyoruz (import).

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


def to_dms(value: float) -> str:
    """
    Ondalik dereceyi "DERECE:DAKIKA:SANIYE.ss" metnine cevirir
    (SYST:STAT?'ta kullanilan format, GPS?'teki DDMM.MMMM'den FARKLI).
    Ornek: 40.78728 -> "40:47:14.208"
    """
    degrees = int(abs(value))
    remainder_minutes = (abs(value) - degrees) * 60
    minutes = int(remainder_minutes)
    seconds = (remainder_minutes - minutes) * 60
    return f"{degrees}:{minutes:02d}:{seconds:06.3f}"


# Uydu tablosu icin SABIT bir PRN (uydu numarasi) havuzu -- gercek
# kullanicinin paylastigi iki ornek ciktidaki PRN'lerden derlendi.
# Gercek bir GPS almanak/yorunge hesabi YAPMIYORUZ -- sadece bu
# havuzdan sirayla secip, El/Az/SS (yukseklik acisi/yon acisi/sinyal
# gucu) icin basit, tekrarlanabilir bir formulle SAYI uyduruyoruz.
# Amac: gercekci GORUNEN ama fiziksel olarak anlamsiz bir tablo.
_PRN_POOL = [1, 2, 3, 4, 8, 9, 17, 19, 28, 31, 32, 40, 41, 307, 308, 312, 313, 319, 326, 329, 333]


def _synthetic_el_az_ss(index: int) -> tuple[int, int, int]:
    """
    Bir uydu satiri icin El (yukseklik acisi 0-89), Az (yon acisi
    0-359), SS (sinyal gucu, kaba bir araligin icinde) uretir.
    Gercek gok mekanigi degil, SADECE indexe bagli, tekrarlanabilir
    bir formul -- her cagrida ayni index icin ayni sayi cikar.
    """
    el = 10 + (index * 7) % 80
    az = (index * 53) % 360
    ss = 15 + (index * 11) % 35
    return el, az, ss


def generate_satellite_table_rows(tracked_count: int, not_tracked_count: int) -> list[str]:
    """
    SYST:STAT?'taki iki sutunlu uydu tablosunun satirlarini uretir:
    sol sutun TAKIP EDILEN uydular (PRN El Az SS), sag sutun sadece
    GORUNEN (takip edilmeyen) uydular (PRN El Az, SS yok).
    Satir sayisi, iki sutundan HANGISI daha uzunsa ona gore belirlenir;
    kisa olan sutun bos birakilir (gercek ciktida da boyleydi).
    """
    tracked_prns = [_PRN_POOL[i % len(_PRN_POOL)] for i in range(tracked_count)]
    not_tracked_prns = [
        _PRN_POOL[(tracked_count + i) % len(_PRN_POOL)] for i in range(not_tracked_count)
    ]

    row_count = max(len(tracked_prns), len(not_tracked_prns))
    rows = []
    for i in range(row_count):
        if i < len(tracked_prns):
            prn = tracked_prns[i]
            el, az, ss = _synthetic_el_az_ss(i)
            left = f"{prn:>3} {el:>3} {az:>3}   {ss:>2}"
        else:
            left = " " * 16

        if i < len(not_tracked_prns):
            prn2 = not_tracked_prns[i]
            el2, az2, _ = _synthetic_el_az_ss(i + 1000)
            right = f"   {prn2:>3} {el2:>3} {az2:>3}"
        else:
            right = ""

        rows.append(left + right)
    return rows


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