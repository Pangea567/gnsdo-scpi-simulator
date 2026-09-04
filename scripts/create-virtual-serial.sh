#!/bin/bash
#
# create-virtual-serial.sh
#
# Bu script, socat kullanarak birbirine bagli iki sahte seri port
# (pseudo-terminal / PTY) yaratir:
#
#   /tmp/gnsdo-client     <----(sahte kablo)---->   /tmp/gnsdo-simulator
#   (test uygulamasi burayi          (bizim simulator programimiz
#    gercek cihazmis gibi acar)       burayi dinler)
#
# Kullanim:
#   ./scripts/create-virtual-serial.sh
#
# Script calistigi surece (foreground'da, Ctrl+C ile durana kadar)
# bu iki port var olmaya devam eder. Baska bir terminalde:
#   - simulator'i baslat:  python3 src/gnsdo_simulator/main.py
#   - test uygulamasini /tmp/gnsdo-client'a baglayabilirsin
#
# Not: Bu portlar gercek /dev/ttyUSBx veya /dev/ttySx cihazlarina
# HICBIR ihtiyac duymaz, tamamen Linux cekirdeginin sagladigi
# sanal (pseudo) terminal ozelligini kullanir.

set -e

CLIENT_LINK="/tmp/gnsdo-client"
SIMULATOR_LINK="/tmp/gnsdo-simulator"

# Onceki calistirmalardan kalma eski linkler varsa temizleyelim,
# yoksa socat "dosya zaten var" diye hata verebilir.
rm -f "$CLIENT_LINK" "$SIMULATOR_LINK"

echo "Sanal seri port cifti olusturuluyor..."
echo "  Client tarafi (test uygulamasi buraya baglanacak): $CLIENT_LINK"
echo "  Simulator tarafi (bizim programimiz buraya baglanacak): $SIMULATOR_LINK"
echo ""
echo "Durdurmak icin Ctrl+C."
echo ""

socat -d -d \
  pty,raw,echo=0,link="$CLIENT_LINK" \
  pty,raw,echo=0,link="$SIMULATOR_LINK"