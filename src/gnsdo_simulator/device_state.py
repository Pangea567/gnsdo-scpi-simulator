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

from dataclasses import dataclass, field
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

    # GPS? komutunun zengin cevabi icin ek alanlar. Gercek cihazin
    # kilavuzunda "konum, hiz, yukseklik" gosterdigi yaziyordu ama
    # tam ornek cikti bulunamadi -- bu yuzden makul, sabit varsayim
    # degerleri kullaniyoruz (Ankara koordinatlari, sabit/duran bir
    # referans cihaz oldugu icin hiz=0). Gercek format bulunursa
    # sadece commands/gps.py'deki formatlama degisir.
    gps_latitude: float = 39.925018
    gps_longitude: float = 32.836956
    gps_altitude_m: float = 850.0
    gps_speed_kmh: float = 0.0

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
    # Gercek cihazin kilavuzuna gore CSAC:SN? formati "YYMMCSNNNNN"
    # (uretim yili+ayi + "CS" + o ayin seri sirasi). Sabit, makul bir
    # ornek deger -- gercek bir uretim tarihi degil.
    csac_serial_number: str = "2103CS04521"

    # MEASure:POWersupply? icin -- gercek cihazda MEAS:VOLT?'tan
    # (TCXO ayar voltaji) FARKLI bir olcum: guc kaynagi giris voltaji.
    power_supply_voltage: float = 12.0

    # Simulator programinin GERCEKTEN ne zaman baslatildigi -- SYNC:HEALTH?
    # hesaplamasinda "calisma suresi < 200 saniye" kontrolu icin kullanilir.
    # field(default_factory=datetime.now): her yeni DeviceState() yaratildiginda
    # OTOMATIK olarak "simdi" ile doldurulur (sabit bir varsayilan deger
    # yerine, cagrildigi anin zamanini yakalar).
    process_started_at: datetime = field(default_factory=datetime.now)

    # DIAG? icin -- gercek cihazin kullanim kilavuzundan alinan
    # gercek formata gore (kullanicinin bulup paylastigi ornek):
    #   EFControl Relative: 0.025000%
    #   EFControl Absolute: 5
    #   Lifetime : +871
    # EFControl = "Electronic Frequency Control", osilatorun ince
    # frekans ayari icin kullanilan kontrol sinyali. Lifetime =
    # cihaz ilk acildigindan beri gecen toplam saat.
    diag_ef_control_relative_percent: float = 0.025000
    diag_ef_control_absolute: int = 5
    # DEGISTI: bu artik sabit bir sayi degil, "baslangic degeri"
    # (config'ten okunan). Gercekten GORUNTULENEN Lifetime, buna
    # simulator'in ne kadar suredir calistigini (process_started_at'tan
    # gecen saat) EKLEYEREK hesaplanir -- bkz. commands/diagnostic.py
    # icindeki current_lifetime_hours() fonksiyonu. Boylece Lifetime
    # artik GERCEKTEN zamanla artiyor, sabit kalmiyor.
    diag_lifetime_base_hours: int = 871

    # Donanim arizasi durumu -- "hardware-error" senaryosu icin.
    # Normalde ariza yok (hardware_fault=False, fault_message="NONE").
    hardware_fault: bool = False
    fault_message: str = "NONE"

    # PTIME? bilesenleri icin -- gercek cihaz kilavuzunda PTIME?'in
    # PTIME:OUTput? ve PTIME:LEAPsecond:ACCumulated? sorgularini da
    # icerdigi belirtiliyor.
    #   ptime_output_enabled: iki cihazi seri kabloyla baglayip zaman
    #     bilgisi paylasma ozelligi acik mi (varsayilan kapali).
    #   leap_second_accumulated: GPS zamani ile UTC arasindaki, GPS'in
    #     1980'den beri biriktirdigi artik saniye farki -- gercek
    #     cihazlarda GNSS alicidan gelir, biz sabit, gercekci bir
    #     deger kullaniyoruz (bu yaziya kadar birikmis deger 18'dir).
    ptime_output_enabled: bool = False
    leap_second_accumulated: int = 18

    # "warming-up" senaryosu icin -- gercek cihazin kullanim kilavuzuna
    # gore CSAC/Rubidium modulunun atomik kilide gecmesi icin gereken
    # gercek isinma suresi "2 dakikadan az" (kilavuz: "less than 2
    # minutes warmup time to atomic lock"). Bu alan None ise normal
    # davranis (sync_locked dogrudan kullanilir); bir zaman degeriyle
    # doluysa, is_locked() fonksiyonu (asagida) bu zamandan itibaren
    # WARMUP_DURATION_SECONDS kadar sure gecince OTOMATIK olarak
    # "kilitli" sayar -- gercek cihazin davranisini taklit eder.
    warmup_started_at: Optional[datetime] = None


# Gercek cihazin kilavuzuna gore: "less than 2 minutes warmup time to
# atomic lock" -- bu yuzden 2 dakika (120 saniye) kullaniyoruz.
WARMUP_DURATION_SECONDS = 120


def is_locked(state: DeviceState) -> bool:
    """
    Cihazin SU AN kilitli olup olmadigini hesaplar. Coklu komut
    (SYNC:LOCKED?, SYNC?, SYST:STAT?, CSAC:STATUS?) AYNI mantigi
    kullansin diye bunu TEK bir yerde topluyoruz.

    - Holdover'daysa kesinlikle kilitli DEGILDIR.
    - "warming-up" senaryosuyla baslatildiysa (warmup_started_at
      doluysa), gercek 2 dakikalik isinma suresi GECENE KADAR kilitli
      degildir; sure gecince OTOMATIK olarak kilitli sayilir -- bunun
      icin state.sync_locked'i elle degistirmemize bile gerek yok,
      her sorguda YENIDEN hesaplaniyor.
    - Diger durumlarda (warmup_started_at yoksa), dogrudan
      state.sync_locked degerine bakilir (config'ten geldigi gibi).
    """
    if state.holdover:
        return False

    if state.warmup_started_at is not None:
        elapsed = (datetime.now() - state.warmup_started_at).total_seconds()
        return elapsed >= WARMUP_DURATION_SECONDS

    return state.sync_locked