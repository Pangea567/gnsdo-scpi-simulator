"""
serial_server.py

Bu modul, sanal (ya da gercek) seri portu acar, gelen SCPI komut
satirlarini okur, SCPIParser'a yonlendirir, ve varsa cevabi geri yazar.

Nasil calisir (ozet):
  1. pyserial kutuphanesi ile port acilir (ornegin /tmp/gnsdo-simulator).
     Ayni kod, gercek bir /dev/ttyUSBx cihaziyla da calisir -- fark yok.
  2. Sonsuz bir donguye girilir: porttan byte byte okunur, "\n" gorunce
     o ana kadar biriken satir tamamlanmis sayilir.
  3. Tamamlanan satir SCPIParser.dispatch() metoduna verilir.
  4. Bir cevap donerse (yani komut biliniyorsa), cevap + "\r\n" olarak
     geri yazilir.
  5. Komut bilinmiyorsa (dispatch None donerse) hicbir sey yazilmaz,
     ama loglanir -- program COKMEZ, sadece devam eder.

Bu tasarimin onemli noktasi: SerialServer, SCPI komutlarinin ne
oldugunu bilmez. O sadece "byte akisini satirlara bol, parser'a ver,
cevabi geri yaz" isini yapar. Hangi komutlarin var oldugu tamamen
SCPIParser'a kayitli handler'lara bagli. Bu sayede ileride yeni komut
eklemek icin bu dosyayi hic degistirmemize gerek kalmayacak.
"""

import logging
import threading
import time

import serial

from gnsdo_simulator.scpi_parser import SCPIParser

# Taninmayan komutlara gercek cihazin verdigi cevap.
UNKNOWN_COMMAND_RESPONSE = "Command Error"

logger = logging.getLogger("gnsdo_simulator.serial_server")


class SerialServer:
    def __init__(
        self,
        port: str,
        parser: SCPIParser,
        baudrate: int = 115200,
        timeout: float = 1.0,
    ) -> None:
        """
        port:     seri port yolu, ornegin "/tmp/gnsdo-simulator"
                   (gercek donanimda "/dev/ttyUSB0" da olabilir, kod
                   degismez)
        parser:   komutlari cevaplara donusturen SCPIParser nesnesi
        baudrate: dokumandaki varsayilan: 115200
        timeout:  serial.read() cagrisinin en fazla ne kadar bekleyecegi
                   (saniye). Bu sayede program veri gelmese bile
                   donguye devam edip Ctrl+C gibi sinyalleri yakalayabilir.
        """
        self.port = port
        self.parser = parser
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: serial.Serial | None = None
        # Normal calisirken (main.py'den) program zaten Ctrl+C ile
        # durduruluyor. Ama TESTLERDE, run_forever()'i bir thread
        # icinde calistirip disaridan "artik dur" diyebilmemiz lazim
        # -- threading.Event tam bunun icin var: bir "bayrak" gibi
        # dusun, set() edilince dongu bir sonraki kontrolde durur.
        self._stop_event = threading.Event()

    def stop(self) -> None:
        """Disaridan run_forever() dongusunu nazikce durdurmak icin."""
        self._stop_event.set()

    def open(self) -> None:
        """Seri portu acar. Gercek cihazda oldugu gibi 8N1, flow control yok."""
        self._serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=self.timeout,
        )
        logger.info("Seri port acildi: %s (baud=%s)", self.port, self.baudrate)

    def close(self) -> None:
        if self._serial is not None and self._serial.is_open:
            self._serial.close()
            logger.info("Seri port kapatildi: %s", self.port)

    def _read_line(self) -> bytes | None:
        """
        Porttan bir satir okur (\\n gorunceye kadar biriktirir).
        Zaman asimi (timeout) icinde satir tamamlanmazsa None doner,
        cagiran dongu bir sonraki iterasyona gecer.
        """
        assert self._serial is not None
        line = self._serial.readline()  # pyserial: timeout'a kadar \n bekler
        if not line:
            return None
        return line

    def run_forever(self) -> None:
        """
        Ana dongu. Ctrl+C (KeyboardInterrupt) GELENE KADAR, ya da
        disaridan stop() cagrilana kadar, surekli porttan okur,
        parser'a verir, cevabi yazar.
        """
        if self._serial is None:
            self.open()

        logger.info("Simulator dinlemede, komut bekleniyor... (durdurmak icin Ctrl+C)")

        try:
            while not self._stop_event.is_set():
                raw_line = self._read_line()
                if raw_line is None:
                    continue  # timeout, veri gelmedi, tekrar dene

                logger.info("RX: %r", raw_line)

                response = self.parser.dispatch(raw_line)

                if response is None:
                    # GERCEK CIHAZ DAVRANISI: taninmayan komutta cihaz
                    # SESSIZ KALMIYOR, "Command Error" donuyor. Bunu
                    # gercek cihaz kayitlarindan ogrendik.
                    #
                    # Nicin onemli: sessiz kalinsa istemci cevabi
                    # bekleyip zaman asimina ugrar ve komutun mu
                    # taninmadigini yoksa baglantinin mi koptugunu
                    # ayirt edemez. Acik bir hata mesaji bu belirsizligi
                    # kaldirir.
                    logger.warning("Bilinmeyen komut: %r", raw_line)
                    response = UNKNOWN_COMMAND_RESPONSE

                out = (response + "\r\n").encode("ascii")
                self._serial.write(out)
                logger.info("TX: %r", out)
        except KeyboardInterrupt:
            logger.info("Durduruluyor (Ctrl+C)...")
        finally:
            self.close()