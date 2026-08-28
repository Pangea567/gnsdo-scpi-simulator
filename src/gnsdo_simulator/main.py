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

from gnsdo_simulator.commands.csac import register_csac_commands
from gnsdo_simulator.commands.diagnostic import register_diagnostic_commands
from gnsdo_simulator.commands.gps import register_gps_commands
from gnsdo_simulator.commands.measure import register_measure_commands
from gnsdo_simulator.commands.ptime import register_ptime_commands
from gnsdo_simulator.commands.sync import register_sync_commands
from gnsdo_simulator.commands.system import register_system_commands
from gnsdo_simulator.device_state import DeviceState
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
        "Simdilik kullanilmiyor, ileride eklenecek.",
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=115200,
        help="Baud rate (varsayilan: 115200)",
    )
    return parser


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    args = build_arg_parser().parse_args()

    device_state = DeviceState()
    scpi_parser = SCPIParser()

    register_system_commands(scpi_parser, device_state)
    register_gps_commands(scpi_parser, device_state)
    register_ptime_commands(scpi_parser)
    register_sync_commands(scpi_parser, device_state)
    register_diagnostic_commands(scpi_parser)
    register_measure_commands(scpi_parser, device_state)
    register_csac_commands(scpi_parser, device_state)

    server = SerialServer(port=args.port, parser=scpi_parser, baudrate=args.baudrate)
    server.run_forever()


if __name__ == "__main__":
    main()