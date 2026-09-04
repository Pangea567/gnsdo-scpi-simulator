"""
main.py

Simulator'in giris noktasi (entry point).

Bu dosya, tum parcalari bir araya getirir:
  1. Bos bir DeviceState (cihaz hafizasi) yaratir.
  2. Bos bir SCPIParser (komut defteri) yaratir.
  3. commands/ klasorundeki register_*_commands() fonksiyonlarini
     cagirarak gercek komutlari parser'a kaydeder.
  4. SerialServer'i bu parser ile baslatir.

Yeni bir komut grubu (ornegin GPS komutlari) eklemek istedigimizde,
tek yapmamiz gereken: commands/gps.py yazmak ve asagiya
"register_gps_commands(scpi_parser, device_state)" satirini eklemek.

Kullanim:
    python3 src/gnsdo_simulator/main.py --port /tmp/gnsdo-simulator
"""

import argparse
import logging
import os

from gnsdo_simulator.commands.csac import register_csac_commands
from gnsdo_simulator.commands.diagnostic import register_diagnostic_commands
from gnsdo_simulator.commands.gps import register_gps_commands
from gnsdo_simulator.commands.measure import register_measure_commands
from gnsdo_simulator.commands.ptime import register_ptime_commands
from gnsdo_simulator.commands.sync import register_sync_commands
from gnsdo_simulator.commands.system import register_system_commands
from gnsdo_simulator.config_loader import load_scenario
from gnsdo_simulator.scpi_parser import SCPIParser
from gnsdo_simulator.serial_server import SerialServer


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GNSDO SCPI Device Simulator")
    parser.add_argument(
        "--port",
        required=True,
        help="Simulator'in dinleyecegi seri port (ornek: /tmp/gnsdo-simulator)",
    )
    parser.add_argument(
        "--scenario",
        default="normal",
        help="Senaryo adi (normal, gnss-lost, holdover, ...). "
        "configs/<isim>.yaml dosyasini yukler.",
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=115200,
        help="Baud rate (varsayilan: 115200)",
    )
    parser.add_argument(
        "--log-file",
        default="logs/simulator.log",
        help="Loglarin ayrica yazilacagi dosya (varsayilan: logs/simulator.log). "
        "Bos string ('') verilirse dosyaya yazma kapatilir, sadece ekrana basilir.",
    )
    return parser


def setup_logging(log_file: str) -> None:
    """
    Loglamayi HEM ekrana (konsol) HEM de bir dosyaya yazacak sekilde
    kurar.

    Neden ikisi birden?
      Ekrana basma, simulator CALISIRKEN ne oldugunu anlik gormek
      icin iyi -- ama terminali kapatirsan ya da cok fazla satir
      akarsa, eski loglar kaybolur. Dokumanin "Logging" maddesi
      (8. Fonksiyonel Gereksinim) aldigi/gonderdigi veriyi KALICI
      olarak loglamamizi istiyor -- bunun icin bir DOSYAYA da
      yazmamiz lazim.

    logging.basicConfig'in "handlers" parametresi, birden fazla
    "hedef" (konsol, dosya, ...) ayni anda kullanmamizi sagliyor.
    Ikisi de AYNI formatta (tarih + seviye + mesaj) yazacak.
    """
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handlers: list[logging.Handler] = [logging.StreamHandler()]  # ekrana basan

    if log_file:
        # Log dosyasinin klasoru (ornegin "logs/") yoksa olustur --
        # yoksa dosyaya yazmaya calisirken hata alirdik.
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    for handler in handlers:
        handler.setFormatter(formatter)

    logging.basicConfig(level=logging.INFO, handlers=handlers)


def main() -> None:
    args = build_arg_parser().parse_args()

    setup_logging(args.log_file)

    logging.info("Senaryo yukleniyor: %s", args.scenario)
    device_state = load_scenario(args.scenario)
    scpi_parser = SCPIParser()

    register_system_commands(scpi_parser, device_state)
    register_gps_commands(scpi_parser, device_state)
    register_ptime_commands(scpi_parser, device_state)
    register_sync_commands(scpi_parser, device_state)
    register_diagnostic_commands(scpi_parser, device_state)
    register_measure_commands(scpi_parser, device_state)
    register_csac_commands(scpi_parser, device_state)

    server = SerialServer(port=args.port, parser=scpi_parser, baudrate=args.baudrate)
    server.run_forever()


if __name__ == "__main__":
    main()