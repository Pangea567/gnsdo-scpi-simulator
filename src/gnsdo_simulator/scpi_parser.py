"""
scpi_parser.py

Bu modul, seri porttan gelen ham SCPI komut satirlarini temizler
(normalize eder) ve dogru komut handler fonksiyonuna yonlendirir.

Nasil calisir (ozet):
  1. Cihaza gelen veri her zaman bayt (bytes) olarak gelir, ornegin:
     b"*IDN?\\r\\n"
  2. normalize_command() bu veriyi okunabilir bir string'e cevirir,
     bastaki/sondaki bosluklari ve satir sonu karakterlerini (\\r, \\n)
     temizler, ve komutu buyuk harfe cevirir (case-insensitive olmasi icin).
  3. SCPIParser sinifi, komut isimlerini (ornegin "*IDN?") ilgili
     Python fonksiyonlarina baglayan bir "kayit defteri" (registry) tutar.
  4. dispatch() metodu, gelen komutu bu deftere bakarak calistirir.
     Eger komut deftere kayitli degilse, program COKMEZ; bunun yerine
     None dondurur (yani "boyle bir komut bilmiyorum").

IKI TUR KOMUT VAR:
  - Query (sorgu) komutlari: "*IDN?", "GPS?" gibi, PARAMETRESIZ,
    sadece bir cevap donerler. register() ile kaydedilirler.
  - Setter (durum degistiren) komutlari: "SYNC:SOUR:MODE GPS" gibi,
    komuttan sonra bir BOSLUK ve bir DEGER gelir. register_setter()
    ile kaydedilirler, handler'lari o degeri parametre olarak alir.
    Bazen (ornegin "SYNC:HOLD:INIT") deger yoktur, sadece komutun
    kendisi bir "aksiyon" tetikler -- bu durumda da register_setter
    kullanilir, handler'a bos string ("") gelir.

KISA VE UZUN KOMUT BICIMLERI:
  Gercek SCPI cihazlarinin kilavuzlarinda komutlar boyle yazilir:
  "SYNChronization:HEAlth?" -- BUYUK harfler ZORUNLU kisaltma,
  kucuk harfler ISTEGE BAGLI uzun ek. Yani hem "SYNC:HEA?" (kisa)
  hem "SYNCHRONIZATION:HEALTH?" (tam/uzun) GECERLI olmali, ikisi de
  AYNI komutu ifade ediyor. register_alias() bunun icin var: bir
  "takma ad"i (genelde uzun veya alternatif kisa yazim), zaten
  kayitli olan "asil" (canonical) komuta baglar. dispatch() bir
  komutu dogrudan bulamazsa, alias listesine de bakar.
"""

from typing import Callable, Optional


# Query handler'i: parametre almaz, bir string doner.
CommandHandler = Callable[[], str]

# Setter handler'i: komuttan sonraki degeri (str olarak) parametre
# alir, isteğe bagli bir cevap donebilir (cogu zaman None -- yani
# "islemi yaptim ama soyleyecek bir sey yok").
SetterHandler = Callable[[str], Optional[str]]


def normalize_command(raw: bytes | str) -> str:
    """
    Ham veriyi (bytes ya da str) temiz, karsilastirilabilir bir komut
    string'ine cevirir.

    - \\r, \\n, \\r\\n hepsini temizler (satir sonu ne olursa olsun calisir)
    - Bastaki/sondaki bosluklari siler
    - Buyuk harfe cevirir (case-insensitive eslesme icin)

    Ornekler:
        normalize_command(b"*idn?\\r\\n")   -> "*IDN?"
        normalize_command("sync:locked?\\n") -> "SYNC:LOCKED?"
        normalize_command("  MEAS:TEMP?  ")  -> "MEAS:TEMP?"
    """
    if isinstance(raw, bytes):
        # Cihazlar genelde ASCII konusur; hatali bayt gelirse programi
        # cokertmemek icin errors="ignore" kullaniyoruz.
        text = raw.decode("ascii", errors="ignore")
    else:
        text = raw

    # \r\n, \r, \n -> hepsini tek tip bosluga cevirip sonra strip ediyoruz
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.strip()
    return text.upper()


class SCPIParser:
    """
    Komutlari fonksiyonlara baglayan basit bir kayit defteri (registry)
    ve dispatcher (yonlendirici).
    """

    def __init__(self) -> None:
        # Query komutlari: {"*IDN?": idn_fonksiyonu, ...}
        self._commands: dict[str, CommandHandler] = {}
        # Setter komutlari: {"SYNC:SOUR:MODE": mode_degistir_fonksiyonu, ...}
        self._setters: dict[str, SetterHandler] = {}
        # Alias'lar: {"SYNCHRONIZATION:HEALTH?": "SYNC:HEA?", ...}
        # Deger, ZATEN _commands ya da _setters icinde kayitli olan
        # "asil" (canonical) komutun adidir.
        self._aliases: dict[str, str] = {}

    def register(self, command: str, handler: CommandHandler) -> None:
        """
        Bir query komutunu bir fonksiyona baglar.

        command: SCPI komutu, ornegin "*IDN?" (biz otomatik buyuk harfe
                 cevirip kaydediyoruz, sen kucuk harfle de yazsan sorun olmaz)
        handler: parametre almayan, str donduren bir fonksiyon
        """
        key = command.strip().upper()
        self._commands[key] = handler

    def register_setter(self, command_prefix: str, handler: SetterHandler) -> None:
        """
        Bir setter (durum degistiren) komutu baglar.

        command_prefix: komutun basi, ornegin "SYNC:SOUR:MODE" (soru
                 isareti YOK -- setter komutlari "?" ile bitmez)
        handler: bir string parametre alan (deger, veya deger yoksa
                 bos string ""), opsiyonel bir cevap donebilen fonksiyon
        """
        key = command_prefix.strip().upper()
        self._setters[key] = handler

    def register_alias(self, alias: str, canonical: str) -> None:
        """
        Bir komutun ALTERNATIF bir yazimini ("alias") kaydeder --
        genelde gercek cihazin UZUN formu (ornegin
        "SYNCHRONIZATION:HEALTH?"), bizim zaten register()/
        register_setter() ile kaydettigimiz KISA/asil (canonical)
        forma (ornegin "SYNC:HEA?") baglanir.

        Onemli: canonical, register()/register_setter() ile ONCEDEN
        kayitli olmasa BILE calisir -- cunku alias cozumlemesi
        dispatch() aninda yapiliyor, kayit sirasi onemli degil.
        Ama pratikte, okunabilirlik icin canonical'i once kaydedip
        alias'i ondan sonra eklemek daha temiz.
        """
        self._aliases[alias.strip().upper()] = canonical.strip().upper()

    def dispatch(self, raw_line: bytes | str) -> Optional[str]:
        """
        Gelen ham satiri normalize eder, once query komutlarina, sonra
        setter komutlarina bakar, varsa calistirip cevabini dondurur.
        Ikisinde de bulunamazsa, ALIAS listesine bakip asil komuta
        yonlendirir.

        Komut hic bilinmiyorsa None doner (exception FIRLATMAZ -> cokme yok).
        """
        command = normalize_command(raw_line)

        if command == "":
            # Bos satir (sadece \r\n gibi) geldiyse cevap verecek bir sey yok
            return None

        # 1) Once tam eslesen bir query komutu var mi diye bak
        handler = self._commands.get(command)
        if handler is not None:
            return handler()

        # 1b) Dogrudan bulunamadi -- ACABA bu, kayitli bir komutun
        #     ALIAS'i mi? (Ornegin "SYNCHRONIZATION:HEALTH?" gelmis,
        #     ama biz "SYNC:HEA?" diye kaydetmisiz.)
        canonical = self._aliases.get(command)
        if canonical is not None:
            handler = self._commands.get(canonical)
            if handler is not None:
                return handler()

        # 2) Yoksa, bu bir "KOMUT DEGER" seklinde bir setter olabilir mi?
        #    Ilk bosluga kadar olan kismi komut, gerisini deger say.
        #    Ornek: "SYNC:SOUR:MODE GPS" -> prefix="SYNC:SOUR:MODE", value="GPS"
        #    Deger yoksa (ornegin "SYNC:HOLD:INIT"), tum satir prefix olur,
        #    value bos string olur.
        if " " in command:
            prefix, value = command.split(" ", 1)
            value = value.strip()
        else:
            prefix, value = command, ""

        setter = self._setters.get(prefix)
        if setter is None:
            # Setter'in de kendi ALIAS'i olabilir (ornegin
            # "SYNCHRONIZATION:SOURCE:MODE GPS" -> "SYNC:SOUR:MODE")
            canonical_prefix = self._aliases.get(prefix)
            if canonical_prefix is not None:
                setter = self._setters.get(canonical_prefix)

        if setter is not None:
            # ONEMLI: setter'in kendisi None donebilir ("soyleyecek bir
            # sey yok" anlaminda), ama dispatch()'in None'u SADECE
            # "boyle bir komut yok" icin kullanmasi lazim -- yoksa
            # serial_server bunu yanlislikla "bilinmeyen komut" sanip
            # oyle loglar. Bu yuzden setter'in None cevabini burada
            # bos string'e ("") ceviriyoruz: "komut TANINDI, ama
            # gonderilecek bir metin yok".
            result = setter(value)
            return result if result is not None else ""

        # 3) Hicbirine uymadi -- bilinmeyen komut
        return None

    def list_commands(self) -> list[str]:
        """
        Su ana kadar register edilmis tum komutlarin (hem query hem
        setter) listesini, alfabetik siralanmis olarak dondurur.

        Bunu ozellikle HELP? komutu icin ekledik: HELP? cevabini
        elle tutulan ayri bir listeden degil, buradan (yani parser'in
        GERCEKTEN bildigi komutlardan) uretecegiz. Boylece yeni bir
        komut grubu (GPS, PTIME, SYNC...) ekledigimizde HELP? otomatik
        guncellenecek, ayri bir listeyi elle guncellemeyi unutma
        riski kalmayacak.
        """
        return sorted(set(self._commands.keys()) | set(self._setters.keys()))