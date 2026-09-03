"""
commands/diagnostic.py

DIAG? -- genel tani/durum bilgisi. Gercek cihazin kullanim
kilavuzundan alinan gercek ornek cikti formatina gore:

    Fault: NONE
    EFControl Relative: 0.025000%
    EFControl Absolute: 5
    Lifetime : +871

GUNCELLEME -- LIFETIME ARTIK GERCEKTEN ARTIYOR:
  Eskiden Lifetime sabit bir sayiydi (config'ten okunan, hic
  degismeyen bir deger). Artik state.diag_lifetime_base_hours
  sadece "BASLANGIC" degeri -- goruntulenen sayi, buna simulator'in
  GERCEKTEN ne kadar suredir calistigini (process_started_at'tan
  gecen saat) EKLEYEREK hesaplaniyor. Yani simulator'i ne kadar
  uzun sure acik tutarsan, Lifetime o kadar artar -- gercek bir
  cihazda oldugu gibi.
"""

from gnsdo_simulator.device_state import DeviceState, elapsed_hours_since_start
from gnsdo_simulator.scpi_parser import SCPIParser


def _current_lifetime_hours(state: DeviceState) -> int:
    """
    O ANKI gercek Lifetime degerini hesaplar: config'ten gelen
    baslangic degeri + simulator'in GERCEKTEN ne kadar suredir
    calistigi (saat cinsinden, tam sayiya yuvarlanmis).
    """
    return state.diag_lifetime_base_hours + int(elapsed_hours_since_start(state))


def make_diag_handler(state: DeviceState):
    def handler() -> str:
        lines = [
            f"EFControl Relative: {state.diag_ef_control_relative_percent:.6f}%",
            f"EFControl Absolute: {state.diag_ef_control_absolute:.6f}",
            f"Lifetime : +{_current_lifetime_hours(state)}",
        ]
        return "\r\n".join(lines)

    return handler


def make_diag_lifetime_handler(state: DeviceState):
    """
    DIAG:LIFE:COUN? -- kilavuzda DIAG?'in icindeki "Lifetime" satirinin
    AYRI, bagimsiz bir sorgu olarak da var oldugu belirtiliyor
    (DIAGnostic:LIFetime:COUNt?). Ayni (artik GERCEKTEN artan) degeri
    tek basina da sorabilmek icin ekliyoruz.
    """

    def handler() -> str:
        return str(_current_lifetime_hours(state))

    return handler


def register_diagnostic_commands(parser: SCPIParser, state: DeviceState) -> None:
    parser.register("DIAG?", make_diag_handler(state))
    parser.register("DIAG:LIFE:COUN?", make_diag_lifetime_handler(state))

    # --- KISA/UZUN FORM ALIAS'LARI (gercek kilavuzdan) ---
    parser.register_alias("DIAGNOSTIC?", "DIAG?")
    parser.register_alias("DIAGNOSTIC:LIFETIME:COUNT?", "DIAG:LIFE:COUN?")
    parser.register_alias("DIAG:LIF:COUN?", "DIAG:LIFE:COUN?")