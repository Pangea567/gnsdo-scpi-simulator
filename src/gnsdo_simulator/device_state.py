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

from gnsdo_simulator.models.holdover import (
    RB_DRIFT_PER_DAY,
    holdover_tint_seconds,
)
from gnsdo_simulator.models.noise import smooth_noise
from gnsdo_simulator.models.warmup import (
    AMBIENT_TEMPERATURE_C,
    GNSS_LOCK_SECONDS,
    SERVO_STATE_LOCKED,
    THERMAL_TIME_CONSTANT_SECONDS,
    servo_state,
    thermal_ramp,
)


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

    # --- HOLDOVER HATA BIRIKIMI MODELI ICIN ALANLAR ---
    # (bkz. models/holdover.py ve docs/tasarim-kararlari.md)
    #
    # locked_tint_seconds: cihaz GPS'e KILITLIYKEN TINT'in ORTALAMA
    #   degeri. Kapali kontrol dongusu TINT'i SIFIRA cektigi icin bu
    #   sifirdir; anlik okuma sifirin ETRAFINDA salinir (jitter
    #   NOISE_PROFILES["tint"] ile veriliyor).
    #
    #   DUZELTILDI: eskiden 12e-9 (sabit pozitif) idi. Gercek cihaz
    #   kayitlari bunun yanlis oldugunu gosterdi -- TINT ARTI VE EKSI
    #   deger aliyor, yani sifir etrafinda salaniyor:
    #       1.133E-08  -7.873E-09  -1.179E-08  9.063E-09  2.672E-09
    #   Hatanin kaynagi kilavuz §1.1'deki "better than 0.2ns AVERAGE
    #   phase accuracy" ifadesini "jitter genligi 0.2 ns" diye
    #   okumakti. "average" kelimesi kilit: ORTALAMA sifira 0.2 ns
    #   yakin demek; anlik okuma cok daha genis salinir.
    #
    # holdover_entry_tint_seconds: holdover'a GIRILDIGI ANDAKI TINT
    #   (modeldeki x0). Faz sureklidir -- GPS kesildiginde faz farki
    #   sifira atlamaz, o an neyse o kalir ve buyumeye ORADAN baslar.
    #   Bu yuzden giris aninda dondurup sakliyoruz.
    #
    # rb_drift_per_day: Rubidyum osilatorun yaslanma/drift hizi
    #   (modeldeki D). Kilavuz §2.9: kilitliyken ADEV 8E-14/gun'e
    #   yaklasiyor.
    #
    # last_holdover_duration_seconds: BITMIS en son holdover'in
    #   suresi. Kilavuz §3.6.1 SYNC:HOLD:DUR?'un holdover disindayken
    #   "onceki holdover"i dondurmesini istiyor.
    locked_tint_seconds: float = 0.0
    holdover_entry_tint_seconds: float = 0.0
    rb_drift_per_day: float = RB_DRIFT_PER_DAY
    last_holdover_duration_seconds: Optional[float] = None

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
    # GERCEK cihaz kayitlarindan (MEAS? ciktilari): PCB sicakligi
    # 46.57 - 52.87 araliginda gozlendi. Kararli durum ust kumede
    # (~52.8); dusuk okumalar isinma sirasinda alinmis olmali --
    # isinma rampasi FAZ 3'te modellenecek.
    temperature_celsius: float = 52.8
    voltage: float = 1.66  # TCXO ayar voltaji (gercek ornek: 1.658-1.672 araligi)
    current: float = 0.42

    # CSAC (Chip Scale Atomic Clock) -- cihazin icindeki kucuk atomik
    # saat modulu. Ayri bir seri numarasi ve kendi sicakligi olur.
    csac_status: str = "RUNNING"
    # CSAC sicakligi ARTIK BAGIMSIZ BIR ALAN DEGIL -- PCB sicakligina
    # BAGLI olarak turetiliyor (bkz. CSAC_PCB_TEMP_OFFSET ve
    # measured_csac_temperature). Bu alan yalnizca geriye donuk
    # uyumluluk ve config icin duruyor; asil hesap turetilmis olandir.
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

    # --- OLCUM GURULTUSU (bkz. models/noise.py) ---
    # Gercek bir cihazda MEAS:TEMP? her sorguda tipatip ayni sayiyi
    # dondurmez; sensor okumasi son hanede surekli oynar. Gurultu
    # VARSAYILAN OLARAK ACIK -- cunku gercek cihaz davranisi budur.
    #
    # noise_scale: tum genlikleri toptan olceklendirir. 0.0 vermek
    #   gurultuyu tamamen kapatir (kesin deger bekleyen testler ve
    #   gercek cihazla birebir karsilastirma icin pratik).
    noise_enabled: bool = True
    noise_scale: float = 1.0

    # --- ISINMA (bkz. models/warmup.py) ---
    # Bu parametreler yalnizca warmup_started_at DOLU iken devreye
    # girer. Yani "normal" senaryo zaten isinmis bir cihazi temsil
    # etmeye devam eder; soguk baslangic "warming-up" senaryosunun isi.
    ambient_temperature_c: float = AMBIENT_TEMPERATURE_C
    thermal_time_constant_s: float = THERMAL_TIME_CONSTANT_SECONDS


# Kilavuz §1.1: "less than 2 minutes warmup time to atomic lock".
#
# ARTIK KILIT KARARI ICIN KULLANILMIYOR. Bu sure ATOMIK kilide aittir;
# SYNC:LOCKED? ise GNSS'e kilitlenmeyi bildirir (§3.6.11) ve o ~20
# dakika surer. Kilit karari models/warmup.py'deki durum makinesinden
# geliyor; bu sabit geriye donuk uyumluluk icin duruyor ve durum
# makinesindeki ATOMIC_LOCK_SECONDS ile ayni degeri tasir.
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
        # DEGISTI: eskiden 120 saniye sonra kilitli sayiyorduk. O sure
        # kilavuz §1.1'deki ATOMIK kilit suresi ("less than 2 minutes
        # warmup time to atomic lock") -- ama SYNC:LOCKED? atomik kilidi
        # degil, kilavuz §3.6.11'e gore "Rubidyum osilatoru kontrol eden
        # PLL"in, yani GNSS'e kilitlenmenin durumunu bildirir. O ise
        # §2.5'e gore tipik olarak 20 dakika surer.
        #
        # Artik dogrudan servo durum makinesine soruyoruz: sadece
        # durum 6 ("Locked, and GNSS active") gercek kilittir.
        # Arada gecilen durum 2 ("kilitleniyor") kilit DEGILDIR.
        return current_servo_state(state) == SERVO_STATE_LOCKED

    return state.sync_locked

def enter_holdover(state: DeviceState, now: Optional[datetime] = None) -> None:
    """
    Cihazi holdover durumuna sokar.

    Nicin ortak bir fonksiyon? Holdover'a IKI ayri yerden giriliyor:
      1. SYNC:HOLD:INIT komutuyla (calisirken)
      2. config_loader ile ("holdover: true" senaryosuyla baslarken)
    Ayni hazirligi iki yerde tekrar yazarsak biri unutulur ve
    senaryolar birbirinden ayrisir. Tek kaynak ilkesi.

    Giriste TINT'i DONDURUYORUZ (x0): faz sureklidir, GPS kesildiginde
    faz farki sifira atlamaz -- o an neyse o kalir ve hata birikimi
    ORADAN baslar.
    """
    now = now or datetime.now()

    # ANLIK okumayi donduruyoruz (jitter dahil), taban degeri degil.
    # DIKKAT -- SIRA: bu cagri holdover bayragi ACILMADAN once
    # yapilmali, yoksa current_tint_seconds() holdover dalina girer
    # ve heniz baslamamis bir birikimi hesaplamaya calisir.
    state.holdover_entry_tint_seconds = current_tint_seconds(state, now)

    state.holdover = True
    state.sync_locked = False
    state.holdover_started_at = now


def exit_holdover(state: DeviceState, now: Optional[datetime] = None) -> None:
    """
    Cihazi holdover'dan cikarir (recovery).

    Cikarken SUREYI SAKLIYORUZ: kilavuz §3.6.1'e gore SYNC:HOLD:DUR?,
    holdover'da DEGILKEN bir onceki holdover'in suresini dondurmelidir.
    Sureyi burada kaydetmezsek o bilgi kaybolur.
    """
    now = now or datetime.now()
    if state.holdover and state.holdover_started_at is not None:
        state.last_holdover_duration_seconds = (
            now - state.holdover_started_at
        ).total_seconds()

    state.holdover = False
    state.sync_locked = True
    state.holdover_started_at = None


def current_tint_seconds(state: DeviceState, now: Optional[datetime] = None) -> float:
    """
    Cihazin SU ANKI TINT degerini (saniye, isaretli) hesaplar.

    Iki farkli rejim vardir ve aralarindaki fark FIZIKSELDIR:

      KILITLI (kapali dongu): servo dongu TINT'i surekli sifira ceker,
        bu yuzden deger kucuk ve sabittir (§1.1).

      HOLDOVER (acik dongu): duzeltme yoktur, osilatorun frekans hatasi
        zamanla ZAMAN hatasina donusur ve BIRIKIR. Birikim modeli
        models/holdover.py icinde (§3.6.1, §3.6.2).

    Bu fonksiyon TEK kaynaktir: SYNC:TINT?, SYNC? ve SYNC:HEALTH?
    hepsi buradan okur, boylece uc cikti birbiriyle tutarli olur.
    """
    now = now or datetime.now()

    if state.holdover and state.holdover_started_at is not None:
        elapsed_seconds = (now - state.holdover_started_at).total_seconds()
        base = holdover_tint_seconds(
            elapsed_seconds=elapsed_seconds,
            entry_tint_seconds=state.holdover_entry_tint_seconds,
            freq_error_estimate=state.freq_error_estimate,
            drift_per_day=state.rb_drift_per_day,
        )
    else:
        base = state.locked_tint_seconds

    # Olcum jitter'i TREND'in USTUNE binir: birikim yavas ve yonlu,
    # jitter ise hizli ve yonsuz. Gercek cihazda da zaman-aralik
    # sayaci her okumada biraz oynar (GNSS 1PPS jitter'i).
    return apply_noise(state, base, "tint", now)


# --- OLCUM GURULTUSU PROFILLERI ---
# Her alan icin (genlik, periyot_saniye).
#
# GENLIKLER UYDURMA DEGIL -- gercek cihaz ciktisinda GOZLENEN
# araliklardan turetildi (ilgili alanlarin yanindaki yorumlara bakiniz):
#     MEAS:VOLT? (TCXO ayar V) : 1.658 - 1.672  -> +/- 0.007
#     MEAS:POW?  (besleme V)   : 11.70 - 11.74  -> +/- 0.02
#     CSAC:TEMP?               : ~54 civarinda  -> +/- 0.25
#     MEAS:TEMP? (PCB)         : ~42.5 civarinda -> +/- 0.3
#
# PERIYOTLAR FIZIKSEL: hepsi ayni hizda oynasaydi yapay gorunurdu.
#     Sicaklik yavas gezinir (dakikalar) -- isil kutle ani degismez.
#     Voltaj/akim hizli titresir (saniyeler) -- elektriksel gurultu.
#     TINT jitter'i cok hizlidir -- GNSS 1PPS jitter'i.
#
# NOT: CSAC sicakligindaki 47 -> 54 TIRMANISI burada YOK. O, kisa
# vadeli gurultu degil ISINMA davranisidir (cihaz 54 civarina cikip
# orada kalir) ve FAZ 3'te isinma rampasi olarak modellenecektir.
# CSAC modulu ile cevresindeki PCB arasindaki sicaklik farki (C).
# GERCEK cihaz kayitlarindaki dort MEAS? ciftinin ortalamasi.
CSAC_PCB_TEMP_OFFSET = 1.32


NOISE_PROFILES = {
    "temperature": (0.35, 420.0),
    "csac_temperature": (0.06, 260.0),
    "voltage": (0.007, 8.0),
    "current": (0.005, 6.0),
    "power_supply": (0.02, 12.0),
    # EFC (Electronic Frequency Control) surekli oynar -- servo dongu
    # osilatoru ayarladikca degisir. Genlik PPT cinsinden: gercek
    # cihaz kayitlarinda dort ardisik DIAG? sorgusu -82, -88, -128,
    # -21 verdi, yani ~50 ppt'lik bir bant.
    "ef_control_absolute": (50.0, 45.0),
    # TINT jitter'i. Genlik GERCEK CIHAZ KAYITLARINDAN: kilitliyken
    # okumalar +/-12 ns bandinda, sifirin iki yaninda geziniyor
    # (1.133E-08, -7.873E-09, -1.179E-08, 9.063E-09, 2.672E-09).
    # Kilavuzdaki "0.2ns average" bu bandin ORTALAMASIDIR, genligi
    # degil -- ilk modelde bu karistirilmisti.
    "tint": (12e-9, 5.0),
}


def elapsed_seconds_since_start(state: DeviceState, now: Optional[datetime] = None) -> float:
    """
    Program baslangicindan beri gecen sure (saniye).

    Gurultu neden DUVAR SAATINI degil bunu kullaniyor: duvar saati
    kullansaydik ayni senaryo iki farkli gunde farkli degerler
    uretirdi ve tekrarlanabilirlik giderdi.
    """
    now = now or datetime.now()
    return (now - state.process_started_at).total_seconds()


def apply_noise(
    state: DeviceState,
    base: float,
    field: str,
    now: Optional[datetime] = None,
) -> float:
    """
    Bir taban degere, o alana ait deterministik gurultuyu ekler.

    TEK KAYNAK: hem MEAS:TEMP? hem de MEAS?'in ozet satiri buradan
    okur, boylece ayni anda sorulunca AYNI degeri gorurler. Iki yerde
    ayri hesap yapsaydik ozet ile tekil sorgu birbirini tutmazdi.
    """
    if not state.noise_enabled or state.noise_scale == 0.0:
        return base

    amplitude, period = NOISE_PROFILES[field]
    elapsed = elapsed_seconds_since_start(state, now)

    return base + amplitude * state.noise_scale * smooth_noise(elapsed, field, period)


def measured_temperature(state: DeviceState, now: Optional[datetime] = None) -> float:
    """
    MEAS:TEMP? -- PCB sicakligi.

    DORT ondalikla donduruluyor: gercek cihaz ciktisi boyle
    ("PCB Temperature: 46.5688", "51.1479"). CSAC sicakligi ise IKI
    ondalik kullaniyor ("54.10") -- ayni cihazda farkli biçimler,
    ama gercek davranis bu.
    """
    taban = current_pcb_temperature_base(state, now)
    return round(apply_noise(state, taban, "temperature", now), 4)


def measured_csac_temperature(state: DeviceState, now: Optional[datetime] = None) -> float:
    """
    CSAC:TEMP? -- CSAC modulu sicakligi.

    BAGIMSIZ DEGIL, PCB SICAKLIGINDAN TURETILIYOR. Gercek cihazin
    MEAS? ciktilarinda ikisi HER ZAMAN birlikte hareket ediyor ve
    aradaki fark neredeyse sabit:

        PCB 46.5688 -> CSAC 47.83   (+1.261)
        PCB 52.7762 -> CSAC 54.10   (+1.324)
        PCB 52.8652 -> CSAC 54.17   (+1.305)
        PCB 49.7419 -> CSAC 51.13   (+1.388)
                              ortalama +1.319

    Fiziksel olarak makul: CSAC modulu isi KAYNAGIDIR, cevresindeki
    kart ondan biraz serindir. Ikisini bagimsiz modelleseydik ters
    yonlere gidebilir ve gercekte hic gorulmeyen kombinasyonlar
    uretebilirlerdi.

    Uzerine kucuk bir bagimsiz jitter ekliyoruz -- ayri sensorler
    oldugu icin fark tipatip sabit degil (1.261 ile 1.388 arasi).
    """
    pcb = apply_noise(state, current_pcb_temperature_base(state, now), "temperature", now)
    csac = pcb + CSAC_PCB_TEMP_OFFSET
    return round(apply_noise(state, csac, "csac_temperature", now), 2)


def measured_rubidium_temperature(state: DeviceState, now: Optional[datetime] = None) -> float:
    """
    MEASure:CURRent? -- ADI YANILTICI, AKIM DONDURMEZ.

    Kilavuz §3.8.3: "Legacy SCPI command, instead of OCXO current this
    command displays either the internal Rubidium temperature or PCB
    temperature around the filter oscillator."

    Gercek cihaz kaydi bunu dogruluyor: MEAS:CURR? -> 51.3210, hemen
    yanindaki MEAS:TEMP? -> 51.1479. Ikisi de SICAKLIK, akim degil.
    (Bizim eski cevabimiz 0.42 idi -- akim sanmisiz.)

    Eski bir komutun adiyla isi arasindaki bu uyumsuzluk gercek
    cihazlarda siktir: komut geriye donuk uyumluluk icin korunur ama
    dondurdugu sey degismistir.
    """
    return round(
        apply_noise(state, current_pcb_temperature_base(state, now), "current", now)
        + CSAC_PCB_TEMP_OFFSET,
        4,
    )


def measured_voltage(state: DeviceState, now: Optional[datetime] = None) -> float:
    """MEAS:VOLT? -- TCXO ayar voltaji (gurultulu)."""
    return round(apply_noise(state, state.voltage, "voltage", now), 3)


def measured_power_supply(state: DeviceState, now: Optional[datetime] = None) -> float:
    """MEASure:POWersupply? -- besleme voltaji (gurultulu)."""
    return round(
        apply_noise(state, state.power_supply_voltage, "power_supply", now), 2
    )


# EFC Absolute ile Relative arasindaki donusum carpani.
#
# GERCEK cihaz kayitlarindaki DORT ornegin TAMAMINDA tutuyor:
#     -0.410000%  ->  -82        -0.440000%  ->  -88
#     -0.640000%  ->  -128       -0.105000%  ->  -21
#
# Yani Absolute = Relative_yuzde * 200. Kilavuz §3.7.1/§3.7.2 ile de
# tutarli: Relative -100%..+100% araliginda, Absolute ise
# parts-per-trillion cinsinden -- tam olcek +/-20000 ppt demek.
#
# Bu ikisini BAGIMSIZ sabitler olarak tutmak yanlisti: birbiriyle
# celisen degerler uretebilirlerdi.
EFC_ABSOLUTE_PER_PERCENT = 200.0


def measured_ef_control_absolute(state: DeviceState, now: Optional[datetime] = None) -> int:
    """
    DIAG? -- EFControl Absolute (parts-per-trillion).

    BU ASIL DEGERDIR ve TAM SAYIDIR. Gercek cihaz kayitlarinda hep
    tam sayi cikiyor: -82, -88, -128, -21. Bunun sebebi muhtemelen
    degerin bir DAC/sayac adimindan gelmesi -- ara deger uretemez.
    """
    base = state.diag_ef_control_relative_percent * EFC_ABSOLUTE_PER_PERCENT
    return int(round(apply_noise(state, base, "ef_control_absolute", now)))


def measured_ef_control_relative(state: DeviceState, now: Optional[datetime] = None) -> float:
    """
    DIAG? -- EFControl Relative (%).

    ABSOLUTE'TAN TURETILIYOR -- tersi degil. Bunu gercek cihaz
    kayitlarindaki degerlerin kendisi soyluyor:

        -82 / 200 = -0.410000       -88 / 200 = -0.440000
       -128 / 200 = -0.640000       -21 / 200 = -0.105000

    Relative degerleri 6 ondalikta TAM cikiyor. Rastgele bir yuzde
    olsaydi bu mumkun olmazdi; demek ki asil deger tam sayi olan
    Absolute ve yuzde ondan hesaplaniyor.

    Ikisini bagimsiz alanlar olarak tutmak yanlisti: birbiriyle
    celisen degerler uretebilirlerdi.
    """
    return measured_ef_control_absolute(state, now) / EFC_ABSOLUTE_PER_PERCENT


def warmup_elapsed_seconds(
    state: DeviceState, now: Optional[datetime] = None
) -> Optional[float]:
    """
    Isinmanin basindan beri gecen sure; cihaz zaten isinmis kabul
    ediliyorsa None.

    NICIN None: "normal" senaryo, coktan isinmis ve kilitlenmis bir
    cihazi temsil eder -- her simulator acilisinda 20 dakika beklemek
    anlamsiz olurdu. Soguk baslangic ayri bir senaryodur
    ("warming-up"), ve orada warmup_started_at dolu gelir.
    """
    if state.warmup_started_at is None:
        return None
    now = now or datetime.now()
    return (now - state.warmup_started_at).total_seconds()


def current_servo_state(state: DeviceState, now: Optional[datetime] = None) -> int:
    """
    SERVo:STATe? degeri (kilavuz §3.10.3).

    TEK KAYNAK: hem SERVo:STATe? hem SYNC:LOCKED? hem de SYST:STAT?
    buradan okur, boylece uc cikti birbiriyle celismez.
    """
    now = now or datetime.now()

    holdover_elapsed = 0.0
    if state.holdover and state.holdover_started_at is not None:
        holdover_elapsed = (now - state.holdover_started_at).total_seconds()

    elapsed = warmup_elapsed_seconds(state, now)
    if elapsed is None:
        # Coktan isinmis: durum makinesine "sure fazlasiyla doldu" de
        elapsed = GNSS_LOCK_SECONDS * 10

    return servo_state(
        elapsed_seconds=elapsed,
        holdover=state.holdover,
        holdover_elapsed_seconds=holdover_elapsed,
        gnss_locked=state.gnss_satellites_tracking >= MIN_SATELLITES_FOR_LOCK,
    )


def current_pcb_temperature_base(
    state: DeviceState, now: Optional[datetime] = None
) -> float:
    """
    PCB sicakliginin GURULTUSUZ taban degeri.

    Isinma sirasinda ustel rampa uzerinde ilerler; isinma bittiginde
    (ya da hic baslamadiysa) kararli calisma sicakligidir.
    """
    elapsed = warmup_elapsed_seconds(state, now)
    if elapsed is None:
        return state.temperature_celsius

    return thermal_ramp(
        elapsed_seconds=elapsed,
        final_temperature=state.temperature_celsius,
        start_temperature=state.ambient_temperature_c,
        time_constant=state.thermal_time_constant_s,
    )
