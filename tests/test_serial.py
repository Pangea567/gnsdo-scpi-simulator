"""
test_serial.py

SerialServer'in gercek bir seri port (PTY) uzerinden GERCEKTEN
calistigini kanitlayan otomatik integration testi.

FARKI NE?
  Su ana kadar bunu ELLE test ediyorduk: bir terminalde socat
  calistirip, baska bir terminalde screen ile baglanip, elle
  komut yazip cevaba bakiyorduk. Bu test, AYNI SEYI, hicbir
  elle mudahale olmadan, `pytest tests/` calistirdiginda otomatik
  yapiyor.

  os.openpty(): Linux'un bize bir PTY (pseudo-terminal) CIFTI
  veren sistem cagrisi -- socat'in arka planda yaptigi seyin
  BIREBIR AYNISI, ama dis bir program (socat) calistirmadan,
  dogrudan Python icinden.

  master_fd: bizim (test/client tarafinin) yazip okuyacagi taraf
  slave_fd / slave_path: SerialServer'in acacagi taraf (tipki
      "/tmp/gnsdo-simulator" gibi, ama gercek adi "/dev/pts/N")

  SerialServer sonsuz bir dongude calistigi icin, onu AYRI BIR
  THREAD (iş parçacığı) icinde baslatiyoruz -- boylece ana test
  kodu, o dongu bitmeden komut gonderip cevap okuyabiliyor.
  Test bitince server.stop() ile dongu nazikce durduruluyor.
"""

import os
import sys
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gnsdo_simulator.device_state import DeviceState
from gnsdo_simulator.scpi_parser import SCPIParser
from gnsdo_simulator.serial_server import SerialServer
from gnsdo_simulator.commands.system import register_system_commands
from gnsdo_simulator.commands.sync import register_sync_commands


def test_serial_pty():
    # 1) Gercek bir PTY cifti ac (socat'in yaptigi seyin ayni)
    master_fd, slave_fd = os.openpty()
    slave_path = os.ttyname(slave_fd)

    # 2) Kucuk bir parser + state hazirla (sadece bu test icin)
    state = DeviceState()
    parser = SCPIParser()
    register_system_commands(parser, state)

    # 3) SerialServer'i, PTY'nin "simulator tarafina" (slave_path)
    #    bagla. timeout'u kucuk tutuyoruz ki test hizli calissin.
    server = SerialServer(port=slave_path, parser=parser, timeout=0.2)

    # 4) Sonsuz donguyu (run_forever) AYRI bir thread'de baslat --
    #    yoksa ana test kodu burada sonsuza kadar takili kalirdi.
    server_thread = threading.Thread(target=server.run_forever, daemon=True)
    server_thread.start()

    time.sleep(0.3)  # server'in portu acmasi icin kisa bir bekleme payi

    try:
        # 5) Client tarafindan (master_fd) bir komut yaz
        os.write(master_fd, b"*IDN?\r\n")
        time.sleep(0.3)

        # 6) Cevabi oku
        response = os.read(master_fd, 200)

        assert b"Jackson Labs" in response
        assert b"LN Rb GPSDO" in response
    finally:
        # 7) Ne olursa olsun (test gecse de patlasa da) server'i
        #    duzgunce durdur, thread'in bitmesini bekle, fd'leri kapat.
        server.stop()
        server_thread.join(timeout=2)
        os.close(master_fd)


def test_serial_pty_unknown_command_does_not_crash_server():
    """
    Gercek PTY uzerinden bilinmeyen bir komut gonderiyoruz, sonra
    tekrar bilinen bir komut gonderip server'in hala ayakta ve
    cevap verir durumda oldugunu kanitliyoruz.
    """
    master_fd, slave_fd = os.openpty()
    slave_path = os.ttyname(slave_fd)

    state = DeviceState()
    parser = SCPIParser()
    register_system_commands(parser, state)
    register_sync_commands(parser, state)

    server = SerialServer(port=slave_path, parser=parser, timeout=0.2)
    server_thread = threading.Thread(target=server.run_forever, daemon=True)
    server_thread.start()
    time.sleep(0.3)

    try:
        os.write(master_fd, b"FOO:BAR:BAZ?\r\n")
        time.sleep(0.3)
        hata_cevabi = os.read(master_fd, 200)

        # GERCEK CIHAZ DAVRANISI: taninmayan komutta cihaz SESSIZ
        # KALMAZ, "Command Error" dondurur (gercek cihaz kayitlarindan).
        # Sessiz kalinsaydi istemci zaman asimina ugrar ve komutun mu
        # taninmadigini yoksa baglantinin mi koptugunu ayirt edemezdi.
        assert hata_cevabi.strip() == b"Command Error"

        os.write(master_fd, b"SYNC:LOCKED?\r\n")
        time.sleep(0.3)
        response = os.read(master_fd, 200)

        # Hatadan SONRA da normal calismaya devam etmeli
        assert response.strip() == b"1"
        assert server_thread.is_alive()  # server hala calisiyor, cokmemis
    finally:
        server.stop()
        server_thread.join(timeout=2)
        os.close(master_fd)
