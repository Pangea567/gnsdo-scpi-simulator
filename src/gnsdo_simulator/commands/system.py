"""
commands/system.py

Sistem ve kimlik komutlari: *IDN?, HELP?, SYST:STAT?

Bu dosyadaki her fonksiyon, SCPIParser'a "register" edilecek bir
handler'dir. Yani her fonksiyon, parametre almadan bir string doner
-- tipki bir onceki adimda yazdigimiz lambda'nin yaptigi gibi, ama
artik gercek, isimli fonksiyonlar olarak ve DeviceState'ten okuyarak.

register_system_commands() fonksiyonu, bu handler'lari parser'a
toplu halde kaydeder. main.py sadece bu tek fonksiyonu cagiracak,
"hangi komutun hangi fonksiyona bagli oldugu" detayini bilmesine
gerek kalmayacak.
"""

from datetime import datetime

from gnsdo_simulator.commands.gps import generate_satellite_table_rows, to_dms
from gnsdo_simulator.device_state import DeviceState, MIN_SATELLITES_FOR_LOCK, is_locked
from gnsdo_simulator.scpi_parser import SCPIParser


def make_idn_handler(state: DeviceState):
    """
    *IDN? komutunun cevabini uretecek fonksiyonu hazirlar.

    Neden fonksiyon-doner-fonksiyon (make_idn_handler icinde
    baska bir fonksiyon tanimliyoruz)?
      Cunku SCPIParser.register() parametre ALMAYAN bir fonksiyon
      bekliyor (hatirla: CommandHandler = Callable[[], str]).
      Ama bizim cevabimiz DeviceState'e bagli (serial_number,
      firmware_version degisebilir). Bu yuzden "state'i bilen, ama
      disariya parametre almayan" bir fonksiyon uretiyoruz. Buna
      "closure" denir: ic taraftaki fonksiyon, dis taraftaki
      degiskenleri (burada: state) hatirlar.

    Gercek cihazin *IDN? formati genelde soyle olur:
      <Uretici>,<Model>,<Seri Numara>,<Firmware>
    """

    def idn_handler() -> str:
        return f"Jackson Labs, LN Rb GPSDO (PRE), Firmware Rev {state.firmware_version}"

    return idn_handler


def make_help_handler(parser: SCPIParser):
    """
    HELP? komutunun cevabini uretecek fonksiyonu hazirlar.

    Ayni closure mantigi: parser'i hatirlayan, parametre almayan
    bir fonksiyon donuyoruz. Onemli detay: bu fonksiyon parser'in
    listesini "register anindaki hali" ile degil, "her cagrildiginda
    GUNCEL hali" ile okur -- cunku parser.list_commands() cagrisi
    fonksiyonun ICINDE, yani HELP? her calistirildiginda tekrar
    calisir. Bu sayede HELP?'i en once register etsek bile, daha
    sonra eklenen GPS/PTIME/SYNC komutlari da listede gorunur.
    """

    def help_handler() -> str:
        return ",".join(parser.list_commands())

    return help_handler


def make_syst_stat_handler(state: DeviceState):
    """
    SYST:STAT? -- GERCEK cihaz ciktisina gore, cok satirlik bir
    "dashboard" raporu: baslik + uydu tablosu + konum/UTC + saglik
    ozeti. Eskiden bu komut tek kelimelik bir durum donuyordu
    ("OK", "FAULT" gibi) -- artik o durum bilgisi, raporun icindeki
    "GPSDO Status" alanina tasindi.

    NOT: Uydu tablosunun (PRN/El/Az/SS) satir araligi/bosluklari
    GERCEK cihazla BIREBIR AYNI OLMAYABILIR -- kullanicinin
    paylastigi ornek metin bir Word belgesinden kopyalanirken hiza
    bozulmus olabilir. Etiketler/alanlar/siralama dogru, ama tam
    piksel hizasi "en iyi caba" (best-effort) seviyesinde.
    """

    def handler() -> str:
        tracking = state.gnss_satellites_tracking
        visible = state.gnss_satellites_visible
        not_tracking = max(0, visible - tracking)
        has_fix = tracking >= MIN_SATELLITES_FOR_LOCK

        now = datetime.now()
        utc_time = f"{now.hour}:{now.minute:02d}:{now.second:02d}"
        utc_date = f"{now.day} {now.strftime('%b')} {now.year}"

        if state.hardware_fault:
            gpsdo_status = "Fault"
        elif state.holdover:
            gpsdo_status = "Holdover"
        elif not is_locked(state):
            gpsdo_status = "Warming Up" if state.warmup_started_at is not None else "Not Locked"
        else:
            gpsdo_status = "Locked"

        fix_status = "3D Fix" if has_fix else "No Fix"

        lines = [
            f"LN Rb GPSDO (PRE)  Serial Number : {state.serial_number}    Hw version : {state.hw_version}",
            "",
            "AQUISITION ................................................",
            f"Tracking:{tracking}        Not Tracking: {not_tracking}",
            "PRN  El  Az   SS   PRN  El  Az",
        ]
        lines.extend(generate_satellite_table_rows(tracking, not_tracking))
        lines.append("")
        lines.append(
            f"LAT   N {to_dms(state.gps_latitude)}             LON   E {to_dms(state.gps_longitude)}"
        )
        lines.append(
            f"HGT   {state.gps_altitude_m:.2f} m (MSL)             UTC    {utc_time}   {utc_date}"
        )
        lines.append("")
        lines.append("HEALTH MONITOR................................................")
        lines.append(f"GPS Receiver Status: {fix_status}             GPSDO Status : {gpsdo_status}")
        lines.append(
            f"1PPS SOURCE MODE  : {state.sync_source_mode}                 "
            f"1PPS SOURCE STATE  : {state.sync_source_state}"
        )
        return "\r\n".join(lines)

    return handler


def register_system_commands(parser: SCPIParser, state: DeviceState) -> None:
    """
    Bu dosyadaki tum sistem komutlarini verilen parser'a kaydeder.

    main.py sadece:
        register_system_commands(scpi_parser, device_state)
    diyecek, detaylari bilmesine gerek yok.
    """
    parser.register("*IDN?", make_idn_handler(state))
    parser.register("HELP?", make_help_handler(parser))
    parser.register("SYST:STAT?", make_syst_stat_handler(state))

    # Kilavuz: "SYSTem:STATus?" -> mandatory SYST+STAT (bizimkiyle
    # ayni), long alias:
    parser.register_alias("SYSTEM:STATUS?", "SYST:STAT?")