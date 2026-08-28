"""
commands/diagnostic.py

DIAG? -- genel tani/hata durumu.

Dokumanda tam format belirtilmemis. Basit bir varsayim yapiyoruz:
cihazda bilinen bir hata yoksa "NO FAULT" donuyoruz. Ileride
"hardware-error" senaryosunu ekledigimizde, DeviceState'e bir
"fault" alani ekleyip bu fonksiyonu ona gore guncelleyecegiz --
degisiklik yine sadece bu dosyada kalacak.
"""

from gnsdo_simulator.scpi_parser import SCPIParser


def diag_handler() -> str:
    return "NO FAULT"


def register_diagnostic_commands(parser: SCPIParser) -> None:
    parser.register("DIAG?", diag_handler)