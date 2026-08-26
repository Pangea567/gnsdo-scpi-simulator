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

from gnsdo_simulator.device_state import DeviceState
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
        return f"Jackson Labs,GNSDO,{state.serial_number},{state.firmware_version}"

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


def syst_stat_handler() -> str:
    """
    SYST:STAT? komutu: cihazin genel durumunu doner.

    SU ANKI ASAMADA basitlestirilmis bir varsayim yapiyoruz: "OK"
    donduruyoruz, cunku henuz GPS/SYNC state'ini eklemedik (o,
    ilerideki adimlarda gelecek). Gercek cihazin kilavuzunda bu
    komutun tam formati varsa (ornegin bir bit-mask ya da farkli
    bir metin), onu gordugumuzde bu fonksiyonu guncelleyecegiz --
    degisiklik yine sadece burada kalacak, baska hicbir yeri
    etkilemeyecek.
    """
    return "OK"


def register_system_commands(parser: SCPIParser, state: DeviceState) -> None:
    """
    Bu dosyadaki tum sistem komutlarini verilen parser'a kaydeder.

    main.py sadece:
        register_system_commands(scpi_parser, device_state)
    diyecek, detaylari bilmesine gerek yok.
    """
    parser.register("*IDN?", make_idn_handler(state))
    parser.register("HELP?", make_help_handler(parser))
    parser.register("SYST:STAT?", syst_stat_handler)
    