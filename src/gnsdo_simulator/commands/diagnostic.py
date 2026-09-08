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

from gnsdo_simulator.device_state import (
    DeviceState,
    elapsed_hours_since_start,
    measured_ef_control_absolute,
    measured_ef_control_relative,
)
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
            f"EFControl Relative: {measured_ef_control_relative(state):.6f}%",
            f"EFControl Absolute: {measured_ef_control_absolute(state):.6f}",
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
    register_diag_efc_queries(parser, state)

    # --- KISA/UZUN FORM ALIAS'LARI (gercek kilavuzdan) ---
    parser.register_alias("DIAGNOSTIC?", "DIAG?")
    parser.register_alias("DIAGNOSTIC:LIFETIME:COUNT?", "DIAG:LIFE:COUN?")
    parser.register_alias("DIAG:LIF:COUN?", "DIAG:LIFE:COUN?")

def make_diag_efc_relative_handler(state: DeviceState):
    """
    DIAGnostic:ROSCillator:EFControl:RELative? (§3.7.1)

    Elektronik frekans kontrolunun (EFC) yuzde cinsinden degeri,
    -100% ile +100% arasinda. DIAG? ozetinde de ayni deger var;
    bu, tek basina sormanin yolu.
    """

    def handler() -> str:
        return f"{measured_ef_control_relative(state):.6f}%"

    return handler


def make_diag_efc_absolute_handler(state: DeviceState):
    """
    DIAGnostic:ROSCillator:EFControl:ABSolute? (§3.7.2)

    Ayni buyuklugun parts-per-trillion (1E-12) cinsinden ifadesi.
    Relative bundan turetilir (Absolute = Relative x 200) -- bkz.
    device_state.EFC_ABSOLUTE_PER_PERCENT.
    """

    def handler() -> str:
        return f"{measured_ef_control_absolute(state):.6f}"

    return handler


def register_diag_efc_queries(parser, state: DeviceState) -> None:
    """
    DIAG alt sisteminin EFC sorgularini kaydeder.

    :ABSolute:CSAC? ve :ABSolute:FILTer? (kilavuz §3.7.3, §3.7.4)
    secili servo dongusune gore ayrisir. Simulatorde tek bir Rubidyum
    dongusu modelledigimiz icin CSAC varyantini ana degere
    baglıyoruz; FILTer varyanti ise kilavuz §3.7.4'e gore VOLT
    cinsindendir, parts-per-trillion degil -- o yuzden ayri bir alan
    kullaniyor.
    """
    parser.register("DIAG:ROSC:EFC:REL?", make_diag_efc_relative_handler(state))
    parser.register("DIAG:ROSC:EFC:ABS?", make_diag_efc_absolute_handler(state))
    parser.register("DIAG:ROSC:EFC:ABS:CSAC?", make_diag_efc_absolute_handler(state))

    parser.register_alias(
        "DIAGNOSTIC:ROSCILLATOR:EFCONTROL:RELATIVE?", "DIAG:ROSC:EFC:REL?"
    )
    parser.register_alias(
        "DIAGNOSTIC:ROSCILLATOR:EFCONTROL:ABSOLUTE?", "DIAG:ROSC:EFC:ABS?"
    )
    parser.register_alias(
        "DIAGNOSTIC:ROSCILLATOR:EFCONTROL:ABSOLUTE:CSAC?", "DIAG:ROSC:EFC:ABS:CSAC?"
    )
