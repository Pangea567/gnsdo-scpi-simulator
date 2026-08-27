"""
device_state.py

Bu modul, simule ettigimiz cihazin "hafizasini" tutar.

Neden ayri bir dosyada?
  Cihazin durumunu (seri numara, firmware, ileride: GPS uydu sayisi,
  senkronizasyon kilitli mi, sicaklik, vb.) TEK bir yerde tutmak
  istiyoruz. Boylece:
    - *IDN? gibi komutlar bu degerleri koddan sabit (hardcoded) okumak
      yerine buradan okur.
    - Ileride config dosyasindan (YAML/JSON) bu degerleri doldurmak
      istedigimizde, sadece burasi degisecek, komut fonksiyonlarina
      dokunmayacagiz.
    - Bir komut state'i degistirdiginde (ornegin ileride
      "SYNC:HOLD:INIT" gibi), bu degisiklik hep ayni DeviceState
      nesnesi uzerinden yapilacak, boylece butun komutlar tutarli
      bir "gercekligi" gorecek.

SU ANKI ASAMADA:
  Sadece kimlik bilgileri var (serial_number, firmware_version).
  GPS, senkronizasyon, sicaklik gibi alanlari ileriki adimlarda,
  ilgili komutlari yazarken buraya ekleyecegiz. Simdiden hepsini
  eklemek yerine, ihtiyac duydukca genisletmek daha kolay takip
  edilebilir olacak.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class DeviceState:
    """
    @dataclass: Python'a "bu bir veri kutusu, otomatik olarak
    __init__ fonksiyonu (kutuyu doldurma fonksiyonu) yaz" demenin
    kisa yolu. Asagidaki iki satir sayesinde otomatik olarak
    su sekilde kullanabiliyoruz:

        state = DeviceState()                     # varsayilan degerlerle
        state = DeviceState(serial_number="X1")    # ozel bir deger vererek
        print(state.serial_number)                 # degere erismek
    """

    serial_number: str = "SIM000001"
    firmware_version: str = "SIM-1.0"

    # GPS/GNSS ile ilgili durum. Gercek cihazda bunlar surekli
    # degisir (uydu gorunurlugu, sinyal kalitesi vb.), ama biz
    # simdilik basit, sabit varsayilan degerlerle basliyoruz.
    # "gnss-lost" gibi senaryolari ekledigimizde, bu degerleri
    # senaryoya gore farkli baslatacagiz.
    gnss_satellites_visible: int = 12
    gnss_satellites_tracking: int = 8

    # Senkronizasyon (SYNC) durumu.
    #   sync_locked: osilator su an referansa (GPS'e) kilitli mi?
    #   holdover: GPS kaybolunca cihaz "son bilinen dogru frekansi
    #             hafizadan calarak" idare etmeye devam eder, buna
    #             holdover denir. holdover=True iken sync_locked=False
    #             olur (cunku artik canli GPS referansi yok).
    #   sync_source_mode: hangi kaynagi kullaniyor ("GPS" gibi).
    #   holdover_started_at: holdover ne zaman basladi (sure hesaplamak
    #             icin). Holdover'da degilse None.
    sync_locked: bool = True
    holdover: bool = False
    sync_source_mode: str = "GPS"
    holdover_started_at: Optional[datetime] = None

    # Olcum (measurement) degerleri -- MEAS:* komutlari icin.
    # Gercekci bir sensor simulasyonu yazmiyoruz, sabit/makul
    # varsayilan degerler kullaniyoruz (dokumandaki ornek degerlerle
    # ayni): sicaklik (C), voltaj (V), akim (A).
    temperature_celsius: float = 42.5
    voltage: float = 12.1
    current: float = 0.42

    # CSAC (Chip Scale Atomic Clock) -- cihazin icindeki kucuk atomik
    # saat modulu. Ayri bir seri numarasi ve kendi sicakligi olur
    # (genelde ana govdeden daha sicak calisir, atomik gecisin
    # gerceklesmesi icin). Sabit, makul varsayim degerleri.
    csac_status: str = "RUNNING"
    csac_temperature_celsius: float = 85.0
    csac_serial_number: str = "CSAC-SIM-0001"