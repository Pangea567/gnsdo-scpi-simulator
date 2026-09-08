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
    """
    PTIME:DATE? -- sadece tarih, "YIL,AY,GUN".
    ONEMLI: gercek cihaz ciktisinda BASTAKI SIFIRLAR YOK (ornek:
    "2026,9,2", "09,02" DEGIL). Bu yuzden strftime'in zero-padding
    yapan %m/%d yerine, sayilari int() ile alip dogrudan yaziyoruz.
    """
    now = datetime.now()
    return f"{now.year},{now.month},{now.day}"


def ptime_time_handler() -> str:
    """
    PTIME:TIME? -- sadece saat, "SAAT,DAKIKA,SANIYE", basta sifir yok.
    Dokumandaki (gorev PDF'i) ornek: PTIME:TIME? -> 20,15,32
    Gercek cihaz ornegi: 7,46,13 (saat tek haneliyse sifirsiz)
    """
    now = datetime.now()
    return f"{now.hour},{now.minute},{now.second}"


def ptime_time_string_handler() -> str:
    """
    PTIME:TIME:STRING? -- okunabilir saat, "SAAT:DAKIKA:SANIYE",
    basta sifir yok. Gercek cihaz ornegi: 7:46:33
    """
    now = datetime.now()
    return f"{now.hour}:{now.minute}:{now.second}"


def make_ptime_output_query_handler(state: DeviceState):
    """
    PTIME:OUTPUT? -- iki cihazi seri kabloyla baglayip zaman
    bilgisi paylasma ozelligi acik mi.

    FORMAT DUZELTMESI: gercek cihaz ciktisinda (PTIME?'in icinde)
    "OUTput :0" seklinde CIPLAK bir 0/1 goruluyor, bizim eski
    "ON"/"OFF" varsayimimiz YANLISTI. Sorgu (query) artik "1"/"0"
    donuyor -- ama setter hala "ON"/"OFF" DEGERINI KABUL EDIYOR
    (kilavuzda setter syntax'i "<ON|OFF>" olarak yaziliyor, bu
    ayri bir sey; sadece SORGUNUN CEVAP formatini duzelttik).
    """

    def handler() -> str:
        return "1" if state.ptime_output_enabled else "0"

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
    PTIME? -- gercek cihaz ciktisina gore ETIKETLI 5 satir:

        DATE :2026,9,2
        TIME :7:15:14
        TINTerval :9.063E-09
        OUTput :0
        LEAPSECOND :18

    ONEMLI: standalone PTIME:DATE?/TIME?/TIME:STRING? sorgulari
    CIPLAK deger doner (etiketsiz) -- SADECE PTIME? bilesimi
    etiketli. Bu yuzden burada parser.dispatch() ile alinan ham
    (etiketsiz) cevaplarin BASINA kendi etiketimizi ekliyoruz.
    """

    def handler() -> str:
        lines = [
            f"DATE :{parser.dispatch('PTIME:DATE?')}",
            f"TIME :{parser.dispatch('PTIME:TIME?')}",
            f"TINTerval :{parser.dispatch('PTIME:TINT?')}",
            f"OUTput :{parser.dispatch('PTIME:OUTPUT?')}",
            f"LEAPSECOND :{parser.dispatch('PTIME:LEAP:ACC?')}",
        ]
        return "\r\n".join(lines)

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
    parser.register("PTIME:LEAP?", make_ptime_leap_handler(state))
    parser.register("PTIME:LEAP:PEND?", make_ptime_leap_pending_handler(state))
    parser.register("PTIME:LEAP:DATE?", make_ptime_leap_date_handler(state))
    parser.register("PTIME:LEAP:DUR?", make_ptime_leap_duration_handler(state))

    parser.register_alias("PTIME:LEAPSECOND?", "PTIME:LEAP?")
    parser.register_alias("PTIME:LEAPSECOND:PENDING?", "PTIME:LEAP:PEND?")
    parser.register_alias("PTIME:LEAPSECOND:DATE?", "PTIME:LEAP:DATE?")
    parser.register_alias("PTIME:LEAPSECOND:DURATION?", "PTIME:LEAP:DUR?")

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

def make_ptime_leap_pending_handler(state: DeviceState):
    """
    PTIMe:LEAPsecond:PENDing? -- bekleyen bir arti saniye var mi (§3.5.7).

    ARTI SANIYE NEDIR: Dunyanin donusu duzensiz oldugu icin, atomik
    zaman (TAI) ile astronomik zaman (UT1) arasindaki fark buyudugunde
    UTC'ye bir saniye eklenir. GNSS alicisi bunu almanaktan ogrenir ve
    onceden haber verir -- zaman kritik sistemler o ani hazirlikli
    karsilasin diye.
    """

    def handler() -> str:
        return "1" if state.leap_second_pending else "0"

    return handler


def make_ptime_leap_date_handler(state: DeviceState):
    """
    PTIMe:LEAPsecond:DATE? -- bekleyen arti saniyenin tarihi (§3.5.9).

    Bekleyen bir olay yoksa cihaz gecerli bir tarih uretmez.
    """

    def handler() -> str:
        return state.leap_second_date

    return handler


def make_ptime_leap_duration_handler(state: DeviceState):
    """
    PTIMe:LEAPsecond:DURation? -- arti saniye gunundeki son dakikanin
    uzunlugu (§3.5.10).

    Kilavuz: "The returned value is 59, 60 or 61 if GPS Almanac data is
    available, and 0 otherwise. A response of 60 indicates that no leap
    second is pending."

    Yani 60 = normal dakika (olay yok), 61 = bir saniye EKLENECEK,
    59 = bir saniye CIKARILACAK.
    """

    def handler() -> str:
        return str(state.leap_second_duration)

    return handler


def make_ptime_leap_handler(state: DeviceState):
    """
    PTIMe:LEAPsecond? -- arti saniye bilgilerinin ozeti.

    BICIM NOTU: Bu komutun ciktisi gercek cihaz kayitlarinda YOK ve
    kilavuz ornek vermiyor. Bicimi, PTIME? ozetindeki etiketli satir
    duzenine benzeterek turettik. Gercek cihazla karsilastirma imkani
    dogarsa once burasi dogrulanmali.
    """

    def handler() -> str:
        return "\r\n".join(
            [
                f"PENDING :{make_ptime_leap_pending_handler(state)()}",
                f"ACCUMULATED :{state.leap_second_accumulated}",
                f"DATE :{state.leap_second_date}",
                f"DURATION :{state.leap_second_duration}",
            ]
        )

    return handler
