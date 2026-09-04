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

    serial_number: str = "122301668"  # gercek cihaz ciktisindan alinan ornek
    # GERCEK cihaz ciktisindan alinan gercek firmware surumu
    # ("Jackson Labs, LN Rb GPSDO (PRE), Firmware Rev 1.17")
    firmware_version: str = "1.17"
    hw_version: str = "1.01.00"  # gercek cihaz ciktisindan (SYST:STAT? basligi icin)

    # GPS/GNSS ile ilgili durum. Gercek cihazda bunlar surekli
    # degisir (uydu gorunurlugu, sinyal kalitesi vb.), ama biz
    # simdilik basit, sabit varsayilan degerlerle basliyoruz.
    # "gnss-lost" gibi senaryolari ekledigimizde, bu degerleri
    # senaryoya gore farkli baslatacagiz.
    gnss_satellites_visible: int = 12
    gnss_satellites_tracking: int = 8

    # GPS? komutunun zengin cevabi icin. GERCEK cihaz ciktisindan
    # (kullanicinin test ettigi konum) alinan gercek enlem/boylam:
    # "N,4047.2368" -> 40 derece + 47.2368 dakika = 40.78728 ondalik
    # "E,2927.2267" -> 29 derece + 27.2267 dakika = 29.45378 ondalik
    gps_latitude: float = 40.78728
    gps_longitude: float = 29.45378
    gps_altitude_m: float = 190.0
    gps_speed_knots: float = 0.0  # gercek cihaz KNOT kullaniyor, km/h degil
    gps_heading_degrees: float = 0.0

    # GPS?'in geri kalan sabit alanlari -- gercek cihaz ciktisindan.
    # Bunlarin cogu "ayar/donanim ozelligi" niteliginde, fix olsun ya
    # da olmasin AYNI kalir (gercek iki farkli ornekte de ayniydi):
    gnss_constellations: str = "GPS SBAS GAL"
    gps_antenna_delay_seconds: float = 2.5e-08
    gps_pulse_sawtooth: float = -6.0  # sadece fix VARKEN gecerli, yoksa 0.0
    gps_dynamic_mode_label: str = "AUTOMATIC(8)"
    gps_dynamic_state_label: str = "STATIONARY(1)"
    gps_survey_min_duration: int = 3600
    gps_survey_variance_limit: int = 150000
    gps_survey_status: str = "ACTIVE"
    gps_survey_duration_seconds: int = 2580  # sadece fix VARKEN, yoksa sabit kucuk deger
    gps_ecef_x: int = 421116328
    gps_ecef_y: int = 237806312
    gps_ecef_z: int = 414469764
    gps_3d_variance: int = 274822336
    gps_timing_mode: str = "RSTSURV"
    # Bu deger GERCEK ciktida fix olsun ya da olmasin AYNIYDI --
    # cihazin bir kere ayarlanmis "hedef" pozisyonu, canli konumdan
    # BAGIMSIZ.
    gps_hold_position: str = "-267998828,-430158341,385929826"
    gps_jamming_level: int = 5
    gps_firmware_version: str = "3.01"

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

    # SYNC? cevabinin geri kalan alanlari icin -- gercek cihaz
    # ciktisindan alinan ek durum bilgileri. Bunlarin cogu "ayar"
    # niteliginde, gercekte de nadiren degisir (kullanici elle
    # degistirmedikce sabit kalirlar) -- o yuzden sabit tutmamiz
    # burada daha az "basitlestirme", daha çok "dogru davranis".
    sync_source_state: str = "GPS"  # "1PPS SOURCE STATE"
    pps_reset_enabled: bool = False  # "1PPS on RESET"
    pps_domain: str = "CSAC"  # "1PPS DOMAIN" -- <CSAC|FILTer>
    phase_noise_filter_enabled: bool = True  # "PHASE NOISE FILTER"
    tint_threshold_ns: int = 220  # "TIME INTERVAL THRESHOLD" (ns)
    # FREQ ERROR ESTIMATE -- gercekte osilatorun anlik frekans sapma
    # tahmini, surekli kucuk oynar. Biz sabit tutuyoruz (bilinçli
    # basitlestirme, MEAS/DIAG alanlarindaki gibi).
    freq_error_estimate: float = 1.31e-11

    # Olcum (measurement) degerleri -- MEAS:* komutlari icin.
    # GUNCELLEME: gercek cihaz ciktisindan ogrendik ki MEAS:VOLT?
    # aslinda TCXO ayar voltaji -- kucuk bir deger (~1.6-1.7V), bizim
    # eski varsayimimiz (12.1V) YANLIS OLCEKTEYDI (guc kaynagi
    # voltajiyla karistirmisiz). Duzelttik.
    temperature_celsius: float = 42.5
    voltage: float = 1.66  # TCXO ayar voltaji (gercek ornek: 1.658-1.672 araligi)
    current: float = 0.42

    # CSAC (Chip Scale Atomic Clock) -- cihazin icindeki kucuk atomik
    # saat modulu. Ayri bir seri numarasi ve kendi sicakligi olur.
    csac_status: str = "RUNNING"
    # Gercek cihaz ciktisinda CSAC Temperature ~47-54 araliginda,
    # PCB sicakligina yakin -- eski varsayimimiz (85.0) cok yuksekti.
    csac_temperature_celsius: float = 54.0
    # GERCEK cihazdan alinan ornek seri numara (kalip: YYMM + harf
    # kodu + 5 haneli sira no). Gercek uretim tarihi degil, ama
    # gercekci bir ornek.
    csac_serial_number: str = "2209MX04906"

    # CSAC?'in tam bilesimi icin -- gercek cihaz ciktisindan alinan
    # ek alanlar (RS232, STEER, MODE, TEC CONTROL, DDS CENTER,
    # DC SIGNAL LEVEL, HEAT PACKAGE, FIRMWARE REV). Bunlarin cogu
    # "ayar/durum" niteliginde, biz sabit tutuyoruz.
    csac_rs232_status: str = "OK"
    csac_steer: float = -71.000
    csac_mode: str = "0x0000"
    csac_tec_control: float = 56.22
    csac_dds_center: float = 0.00
    csac_dc_signal_level: float = 1.00
    csac_heat_package: float = 2730.00
    csac_firmware_rev: str = "V1.0.23"
    # CSAC:LIFEtime? -- DIAG?'in Lifetime'ina benzer sekilde, bu da
    # BASLANGIC degeri + simulator'in gercek calisma suresi olarak
    # hesaplanacak (bkz. device_state.elapsed_hours_since_start()).
    csac_lifetime_base_hours: int = 11247

    # MEASure:POWersupply? -- guc kaynagi giris voltaji (TCXO'dan
    # AYRI, gercek cihaz ciktisinda ~11.7-11.74V araliginda).
    power_supply_voltage: float = 11.7

    # Simulator programinin GERCEKTEN ne zaman baslatildigi -- SYNC:HEALTH?
    # hesaplamasinda "calisma suresi < 200 saniye" kontrolu icin kullanilir.
    # field(default_factory=datetime.now): her yeni DeviceState() yaratildiginda
    # OTOMATIK olarak "simdi" ile doldurulur (sabit bir varsayilan deger
    # yerine, cagrildigi anin zamanini yakalar).
    process_started_at: datetime = field(default_factory=datetime.now)

    # DIAG? icin -- gercek cihazin GERCEK ciktisindan (kullanicinin
    # elle test edip paylastigi ornekler):
    #   EFControl Relative: -0.410000%
    #   EFControl Absolute: -82.000000
    #   Lifetime : +0
    # ONEMLI DUZELTME: gercek ciktida "Fault:" diye bir satir YOK --
    # bizim eski varsayimimiz (biz uydurmustuk) yanlismis, kaldirdik.
    # Ayrica EFControl Absolute gercekte ONDALIKLI (float), bizim
    # eski varsayimimiz (int) yanlisti.
    # EFControl = "Electronic Frequency Control", osilatorun ince
    # frekans ayari icin kullanilan kontrol sinyali. Lifetime =
    # cihaz ilk acildigindan beri gecen toplam saat.
    diag_ef_control_relative_percent: float = -0.410000
    diag_ef_control_absolute: float = -82.000000
    # DEGISTI: bu artik sabit bir sayi degil, "baslangic degeri"
    # (config'ten okunan). Gercekten GORUNTULENEN Lifetime, buna
    # simulator'in ne kadar suredir calistigini (process_started_at'tan
    # gecen saat) EKLEYEREK hesaplanir -- bkz. commands/diagnostic.py
    # icindeki current_lifetime_hours() fonksiyonu. Boylece Lifetime
    # artik GERCEKTEN zamanla artiyor, sabit kalmiyor.
    diag_lifetime_base_hours: int = 871

    # Donanim arizasi durumu -- "hardware-error" senaryosu icin.
    # Normalde ariza yok (hardware_fault=False). NOT: fault_message
    # su an hicbir komutun ciktisinda GORUNMUYOR (gercek cihazin
    # DIAG? ciktisinda boyle bir alan olmadigini gorduk) -- sadece
    # SYST:STAT?'in "FAULT" durumunu tetiklemek icin hardware_fault
    # kullaniliyor. fault_message ileride bir yerde gosterilebilir
    # diye saklaniyor.
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

# Gercek GPS alicilarinin konum hesaplayabilmesi (yani "fix" sahibi
# olabilmesi) icin genelde en az 4 uyduyu ES ZAMANLI takip etmesi
# gerekir. BURADA tutulmasinin sebebi: hem GPS?'in "fix var mi"
# hesabi hem de is_locked()'in "GPS fix'i olmadan osilator kilitlenemez"
# kontrolu AYNI esik degerini kullansin -- iki yerde farkli sayilar
# olursa (biri 4 biri 5 gibi) tutarsizlik cikar, TEK kaynaktan okuyoruz.
MIN_SATELLITES_FOR_LOCK = 4


def elapsed_hours_since_start(state: DeviceState) -> float:
    """
    Simulator'in GERCEKTEN ne kadar suredir calistigini (saat
    cinsinden) hesaplar. Hem DIAG?'in Lifetime'i hem de CSAC?'in
    LIFETIME'i icin ayni mantigi kullanmak amaciyla buraya, ORTAK
    bir yere koyduk -- iki yerde ayni hesaplamayi tekrar yazmiyoruz.
    """
    return (datetime.now() - state.process_started_at).total_seconds() / 3600.0


def is_locked(state: DeviceState) -> bool:
    """
    Cihazin SU AN kilitli olup olmadigini hesaplar. Coklu komut
    (SYNC:LOCKED?, SYNC?, SYST:STAT?, CSAC:STATUS?) AYNI mantigi
    kullansin diye bunu TEK bir yerde topluyoruz.

    Oncelik sirasi (ilk uyan kazanir):
      1. Holdover'daysa kesinlikle kilitli DEGILDIR.
      2. GPS FIX YOKSA (yeterli uydu takip edilmiyorsa) kesinlikle
         kilitli OLAMAZ -- gercek dunyada osilator, GPS'in verdigi
         zaman referansi olmadan kendini ayarlayamaz. (Bu kontrol
         SONRADAN EKLENDI: eskiden is_locked() tracking sayisina
         hic bakmiyordu, bu da "No Fix ama Locked" gibi GERCEKTE
         imkansiz bir kombinasyona izin veriyordu.)
      3. "warming-up" senaryosuyla baslatildiysa (warmup_started_at
         doluysa), gercek 2 dakikalik isinma suresi GECENE KADAR
         kilitli degildir; sure gecince OTOMATIK olarak kilitli
         sayilir.
      4. Diger durumlarda, dogrudan state.sync_locked degerine bakilir.
    """
    if state.holdover:
        return False

    if state.gnss_satellites_tracking < MIN_SATELLITES_FOR_LOCK:
        return False

    if state.warmup_started_at is not None:
        elapsed = (datetime.now() - state.warmup_started_at).total_seconds()
        return elapsed >= WARMUP_DURATION_SECONDS

    return state.sync_locked