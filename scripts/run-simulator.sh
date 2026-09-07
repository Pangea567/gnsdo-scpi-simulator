#!/bin/bash
#
# run-simulator.sh
#
# Simulator'i kolayca baslatmak icin kucuk bir sarmalayici (wrapper).
# PYTHONPATH'i ve varsayilan portu ayarlar, geri kalan tum argumanlari
# oldugu gibi main.py'ye aktarir.
#
# Kullanim ornekleri:
#   ./scripts/run-simulator.sh                       # normal senaryo, /tmp/gnsdo-simulator
#   ./scripts/run-simulator.sh --scenario holdover   # baska bir senaryo
#   ./scripts/run-simulator.sh --port /dev/ttyUSB0   # gercek bir seri port
#
# Onaykosul: once ./scripts/create-virtual-serial.sh calistirilmis
# (veya gercek bir seri port takili) olmali.

set -euo pipefail

# Script nerede olursa olsun repo kok dizinine gec (boylece configs/
# ve src/ gorece yollari her zaman dogru calisir).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

DEFAULT_PORT="/tmp/gnsdo-simulator"

# Kullanici --port vermediyse varsayilani ekle.
if [[ "$*" != *"--port"* ]]; then
  set -- --port "$DEFAULT_PORT" "$@"
fi

export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m gnsdo_simulator.main "$@"
