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

from gnsdo_simulator.device_state import DeviceState, is_locked
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


def make_syst_stat_handler(state: DeviceState):
    """
    SYST:STAT? komutu: cihazin genel durumunu doner.

    Artik SABIT "OK" DEGIL -- state'e bakarak durumu turetiyoruz.
    Oncelik sirasi onemli (yukaridan asagiya, ilk uyan kazanir):
      1. Donanim arizasi varsa            -> "FAULT"
      2. Holdover'daysa                   -> "HOLDOVER"
      3. warming-up senaryosu, hala isiniyor -> "WARMING UP"
         (bkz. device_state.is_locked() -- gercek cihaza gore 2
         dakikalik isinma suresi henuz gecmemis)
      4. Kilitli degil (baska sebep)      -> "NOT LOCKED"
      5. Hicbiri degilse                  -> "OK"

    Bu sayede farkli senaryolarla (--scenario) baslatilan simulator,
    SYST:STAT?'a GERCEKTEN farkli cevaplar verir.
    """

    def handler() -> str:
        if state.hardware_fault:
            return "FAULT"
        if state.holdover:
            return "HOLDOVER"
        if not is_locked(state):
            if state.warmup_started_at is not None:
                return "WARMING UP"
            return "NOT LOCKED"
        return "OK"

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