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


# HELP? komutu, kullanicinin/gelistiricinin hangi komutlarin
# desteklendigini gorebilmesi icin var. Yeni bir komut eklediginde
# bu listeye de eklemeyi unutma -- ileride bunu otomatik hale
# getirebiliriz (parser'in kendi kayitli komut listesinden uretmek
# gibi), ama simdilik MVP icin elle tutulan bir liste yeterli.
SUPPORTED_COMMANDS = [
    "*IDN?",
    "HELP?",
    "SYST:STAT?",
]


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


def help_handler() -> str:
    """
    HELP? komutu: desteklenen komutlarin listesini virgulle
    ayirip tek bir satir olarak dondurur.

    Not: gercek cihazlarda HELP? formati degisebilir (bazen
    her komut ayri satirda gelir). Simdilik basit tutuyoruz,
    gercek cihazin kilavuzuna bakildiginda format farkli
    cikarsa kolayca degistirebiliriz -- degisiklik sadece
    bu fonksiyonun icinde kalacak.
    """
    return ",".join(SUPPORTED_COMMANDS)


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
    parser.register("HELP?", help_handler)
    parser.register("SYST:STAT?", syst_stat_handler)

    