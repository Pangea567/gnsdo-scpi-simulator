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

