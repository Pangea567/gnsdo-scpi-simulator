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
"""

from typing import Callable, Optional


# Bir komut handler'i su imzada olmali: () -> str
# (Ileride parametre alan komutlar icin bunu genisletecegiz,
#  simdilik MVP asamasinda sadece query (?) komutlarla basliyoruz.)
CommandHandler = Callable[[], str]


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
        # Ornek: {"*IDN?": idn_fonksiyonu, "SYNC:LOCKED?": sync_locked_fonksiyonu}
        self._commands: dict[str, CommandHandler] = {}

    def register(self, command: str, handler: CommandHandler) -> None:
        """
        Bir komutu bir fonksiyona baglar.

        command: SCPI komutu, ornegin "*IDN?" (biz otomatik buyuk harfe
                 cevirip kaydediyoruz, sen kucuk harfle de yazsan sorun olmaz)
        handler: parametre almayan, str donduren bir fonksiyon
        """
        key = command.strip().upper()
        self._commands[key] = handler

    def dispatch(self, raw_line: bytes | str) -> Optional[str]:
        """
        Gelen ham satiri normalize eder, kayitli komutlar arasinda arar,
        varsa calistirip cevabini dondurur.

        Komut bilinmiyorsa None doner (exception FIRLATMAZ -> cokme yok).
        """
        command = normalize_command(raw_line)

        if command == "":
            # Bos satir (sadece \r\n gibi) geldiyse cevap verecek bir sey yok
            return None

        handler = self._commands.get(command)
        if handler is None:
            # Bilinmeyen komut: sessizce None donuyoruz.
            # (Ust katmanda bunu loglayacagiz, ama simulator asla crash olmayacak)
            return None

        return handler()

    def list_commands(self) -> list[str]:
        """
        Su ana kadar register edilmis tum komutlarin listesini,
        alfabetik siralanmis olarak dondurur.

        Bunu ozellikle HELP? komutu icin ekledik: HELP? cevabini
        elle tutulan ayri bir listeden degil, buradan (yani parser'in
        GERCEKTEN bildigi komutlardan) uretecegiz. Boylece yeni bir
        komut grubu (GPS, PTIME, SYNC...) ekledigimizde HELP? otomatik
        guncellenecek, ayri bir listeyi elle guncellemeyi unutma
        riski kalmayacak.
        """
        return sorted(self._commands.keys())
    