"""
commands/ptime.py

Zaman/tarih komutlari: PTIME?, PTIME:DATE?, PTIME:TIME?, PTIME:TIME:STRING?

Onemli fark: bu komutlar DeviceState'e IHTIYAC DUYMUYOR. Cunku
cevaplari cihazin "hafizasindan" degil, dogrudan bilgisayarin
sistem saatinden okuyoruz (dokuman da bunu istiyor: "sistem
saatinden dinamik uretilmeli"). Bu yuzden asagidaki fonksiyonlar
commands/system.py ve commands/gps.py'deki gibi bir "closure"a
(state'i hatirlayan ic fonksiyona) ihtiyac duymuyor, dogrudan
kaydedilebiliyorlar.

Python'da "su an ne zaman" bilgisini almak icin datetime modulunu
kullaniyoruz:

    from datetime import datetime
    simdi = datetime.now()   # su anki tarih+saat bilgisini tasiyan bir nesne
    simdi.strftime("%H:%M:%S")  # bunu istedigimiz metin formatina cevirir

strftime = "string format time" -- yani "zamani metne cevir".
Kullandigimiz kod harfleri:
    %Y -> yil (2026)   %m -> ay (08)   %d -> gun (26)
    %H -> saat (20)    %M -> dakika (15)   %S -> saniye (32)
"""

from datetime import datetime

from gnsdo_simulator.scpi_parser import SCPIParser


def ptime_handler() -> str:
    """
    PTIME? -- genel zaman sorgusu. Formati dokumanda ornekle
    verilmemis, biz tarih+saati birlikte donduren makul bir
    varsayim yapiyoruz: "YIL,AY,GUN,SAAT,DAKIKA,SANIYE".
    Gercek cihazin kilavuzunda farkli bir format gorursen, sadece
    bu fonksiyonu degistirmen yeterli.
    """
    now = datetime.now()
    return now.strftime("%Y,%m,%d,%H,%M,%S")


def ptime_date_handler() -> str:
    """PTIME:DATE? -- sadece tarih, "YIL,AY,GUN" (dokumandaki PTIME:TIME?
    ornegindeki virgullu format ile tutarli olsun diye)."""
    now = datetime.now()
    return now.strftime("%Y,%m,%d")


def ptime_time_handler() -> str:
    """
    PTIME:TIME? -- sadece saat, "SAAT,DAKIKA,SANIYE".
    Dokumandaki ornek: PTIME:TIME? -> 20,15,32
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


def register_ptime_commands(parser: SCPIParser) -> None:
    """
    Bu dosyadaki tum PTIME komutlarini verilen parser'a kaydeder.

    Dikkat: diger register_*_commands fonksiyonlarindan farkli
    olarak burada "state" parametresi YOK -- cunku bu komutlar
    DeviceState'e degil, sistem saatine bakiyor.
    """
    parser.register("PTIME?", ptime_handler)
    parser.register("PTIME:DATE?", ptime_date_handler)
    parser.register("PTIME:TIME?", ptime_time_handler)
    parser.register("PTIME:TIME:STRING?", ptime_time_string_handler)
    