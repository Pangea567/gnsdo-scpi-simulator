"""
commands/sync.py

Senkronizasyon komutlari: SYNC?, SYNC:LOCKED?, SYNC:TINT?, SYNC:HEALTH?,
ve durum degistiren (setter) komutlar: SYNC:HOLD:INIT, SYNC:HOLD:REC:INIT,
SYNC:SOUR:MODE <deger>, ve bir sorgu: SYNC:HOLD:DUR?

HOLDOVER NEDIR (kisa hatirlatma):
  Cihaz normalde GPS'e "kilitli" calisir. GPS sinyali kesilirse,
  cihaz oylece durmaz -- son bilinen dogru frekansi kullanarak
  calismaya devam eder, buna "holdover" denir.

GUNCELLEME -- is_locked() KULLANIMI:
  Eskiden kilit durumunu dogrudan state.sync_locked'tan okuyorduk.
  Artik device_state.py'deki ORTAK is_locked(state) fonksiyonunu
  kullaniyoruz -- cunku "warming-up" senaryosunda kilit durumu
  ARTIK ZAMANA BAGLI (gercek cihazin 2 dakikalik isinma suresi
  gecince kendiliginden kilitleniyor). Bu mantigi TEK bir yerde
  tutarak, SYNC:LOCKED?, SYNC?, SYST:STAT?, CSAC:STATUS? hepsi
  AYNI, tutarli kilit durumunu gorur.
"""

from datetime import datetime
from typing import Optional

from gnsdo_simulator.device_state import (
    MIN_SATELLITES_FOR_LOCK,
    DeviceState,
    current_tint_seconds,
    filter_tint_seconds,
    is_filter_loop_locked,
    measured_freq_error_estimate,
    short_term_drift_seconds,
    enter_holdover,
    exit_holdover,
    is_locked,
)
from gnsdo_simulator.scpi_parser import SCPIParser


def make_sync_handler(state: DeviceState):
    """
    SYNC? -- GERCEK cihaz ciktisina gore ETIKETLI 12 satir. Dikkat:
    cogu satiri, ZATEN ASAGIDA tanimli olan diger fonksiyonlari
    (make_sync_hold_dur_handler, make_sync_health_handler,
    _tint_seconds) DOGRUDAN CAGIRARAK olusturuyoruz -- ayni mantigi
    iki yerde tekrar yazmiyoruz. (Python'da bir fonksiyonun govdesi
    icinde, dosyada DAHA ASAGIDA tanimlanmis baska bir fonksiyonu
    cagirmak sorun degil -- cunku bu govde sadece dispatch anida,
    yani dosyanin tamami yuklendikten COK SONRA, calisir.)

    Ornek gercek cikti:
        1PPS SOURCE MODE  : GPS
        1PPS SOURCE STATE : GPS
        1PPS on RESET : OFF
        1PPS DOMAIN : CSAC
        1PPS LOCK STATUS  : 1
        HOLDOVER STATE: NONE
        LAST HOLDOVER DURATION : 191,0
        FREQ ERROR ESTIMATE : 1.31E-11
        TIME INTERVAL DIFFERENCE : 1.133E-08
        TIME INTERVAL THRESHOLD : 220
        PHASE NOISE FILTER : ON
        HEALTH STATUS : 0x0
    """

    def handler() -> str:
        lock_status = "1" if is_locked(state) else "0"
        holdover_state = "ACTIVE" if state.holdover else "NONE"
        pps_reset = "ON" if state.pps_reset_enabled else "OFF"
        phase_filter = "ON" if state.phase_noise_filter_enabled else "OFF"

        lines = [
            f"1PPS SOURCE MODE  : {state.sync_source_mode}",
            f"1PPS SOURCE STATE : {state.sync_source_state}",
            f"1PPS on RESET : {pps_reset}",
            f"1PPS DOMAIN : {state.pps_domain}",
            f"1PPS LOCK STATUS  : {lock_status}",
            f"HOLDOVER STATE: {holdover_state}",
            f"LAST HOLDOVER DURATION : {make_sync_hold_dur_handler(state)()}",
            f"FREQ ERROR ESTIMATE : {measured_freq_error_estimate(state):.2E}",
            f"TIME INTERVAL DIFFERENCE : {_tint_seconds(state):.3E}",
            f"TIME INTERVAL THRESHOLD : {state.tint_threshold_ns}",
            f"PHASE NOISE FILTER : {phase_filter}",
            f"HEALTH STATUS : {make_sync_health_handler(state)()}",
        ]
        return "\r\n".join(lines)

    return handler


def make_sync_locked_handler(state: DeviceState):
    """SYNC:LOCKED? -- "1" (kilitli) ya da "0" (kilitli degil)."""

    def handler() -> str:
        return "1" if is_locked(state) else "0"

    return handler


def _tint_seconds(state: DeviceState) -> float:
    """
    TINT degerini SANIYE cinsinden hesaplar -- hem SYNC:TINT? cevabini
    hem SYNC?'in ilgili satirini hem de SYNC:HEALTH?'in faz kontrolunu
    besler, boylece uc cikti birbiriyle tutarli olur.

    DEGISTI: eskiden holdover'da SABIT 850 ns donduruyordu -- sanki
    hata BIRIKMIYORMUS gibi. Bu fiziksel olarak yanlisti: holdover'da
    kontrol dongusu ACIKTIR, duzeltme gelmez ve hata zamanla buyur.
    Artik hesap device_state.current_tint_seconds() uzerinden
    models/holdover.py'deki birikim modeline yapiliyor.
    """
    return current_tint_seconds(state)


def make_sync_tint_handler(state: DeviceState):
    """
    SYNC:TINT? -- "time interval error", yani referansla aradaki
    zaman farkinin olcumu (saniye cinsinden).

    FORMAT DUZELTMESI: gercek cihaz ciktisi BILIMSEL GOSTERIM
    kullaniyor (ornek: "6.763E-08", "9.063E-09") -- bizim eski
    ondalikli formatimiz ("0.000000012") YANLISTI. Duzelttik.
    Karmasik bir olcum modeli KURMUYORUZ (proje kararimiz geregi):
    sabit degerler kullaniyoruz (bkz. _tint_seconds), sadece
    GORUNUM formatini gercege uydurduk.
    """

    def handler() -> str:
        return f"{_tint_seconds(state):.3E}"

    return handler


def make_sync_health_handler(state: DeviceState):
    """
    SYNC:HEALTH? -- GERCEK cihazin kilavuzuna gore bu SABIT bir
    "GOOD"/"DEGRADED" metni DEGIL, bir HEX BIT-MASK. Her bit, ayri
    bir sorunu isaret ediyor, birden fazla sorun varsa bitler
    'OR'lanarak (bit-bazinda birlestirilerek) tek bir sayida
    toplaniyor. Kilavuzdaki bit tanimlarindan bizim su an
    simule EDEBILDIKLERIMIZ (digerleri -- jamming, filter loop,
    frequency estimate -- henuz simule etmiyoruz, o bitler hep 0):

        0x4     faz farki (TINT) > 210ns
        0x8     calisma suresi < 200 saniye (yeni acilmis)
        0x10    holdover suresi > 60 saniye
        0x100   kisa donem drift (ADEV @ 100s) > 100ns
        0x400   donanim/osilator arizasi (hardware_fault)
        0x800   guclu jamming (>=50) VE GNSS fix yok
        0x1000  filtre osilator dongusu kilitli degil

    HENUZ URETMEDIGIMIZ IKI BIT ve nedenleri:
        0x20   "Frequency Estimate is out of bounds" -- kilavuz bir
               ESIK DEGERI VERMIYOR. Uydurmak yerine uretmiyoruz.
        0x200  "first 3 minutes after a phase-reset" -- jam-sync /
               faz-reset davranisini henuz modellemiyoruz (§3.6.19).

    0x0 = "duzgun kilitli ve isinmis, tamamen saglikli" (kilavuzun
    kendi tanimi).
    """

    def handler() -> str:
        health = 0

        # DIKKAT -- abs(): kilavuz §3.6.18 "if the phase offset to
        # reference is >210ns" diyor; offset bir BUYUKLUKTUR, isaretten
        # bagimsizdir. Eskiden isaretli karsilastirma yapiyorduk, bu da
        # osilator referansin GERISINE dustugunde (TINT negatif) 210
        # ns'yi asan hatalari KACIRIYORDU.
        if abs(_tint_seconds(state)) > 210e-9:
            health |= 0x4

        runtime_seconds = (datetime.now() - state.process_started_at).total_seconds()
        if runtime_seconds < 200:
            health |= 0x8

        if state.holdover and state.holdover_started_at is not None:
            holdover_seconds = (datetime.now() - state.holdover_started_at).total_seconds()
            if holdover_seconds > 60:
                health |= 0x10

        # 0x100 -- kisa donem drift (ADEV @ 100s) > 100 ns (§3.6.18).
        # Kilitliyken kapali dongu bunu sifirda tutar; holdover'da
        # dogrudan birikim hizina baglidir.
        if short_term_drift_seconds(state) > 100e-9:
            health |= 0x100

        if state.hardware_fault:
            health |= 0x400

        # 0x800 -- guclu jamming VE GNSS fix kaybi (§3.6.18, §3.3.28).
        # Kilavuz §3.3.28: "Any level exceeding 50 in combination to
        # loss of GNSS lock will cause a SYNC:HEALTH 0x800 event".
        # DIKKAT: iki kosul BIRLIKTE saglanmali -- sadece jamming
        # yuksekse ama fix devam ediyorsa bayrak yanmaz.
        if (
            state.gps_jamming_level >= 50
            and state.gnss_satellites_tracking < MIN_SATELLITES_FOR_LOCK
        ):
            health |= 0x800

        # 0x1000 -- filtre osilator dongusu kilitli degil (§3.6.18).
        # Kilavuz bunu "with Rubidium oscillator loop selected only"
        # diye sinirliyor, o yuzden secili dongu CSAC (Rubidyum)
        # degilse bayragi hic uretmiyoruz.
        if state.servo_selected_loop == "CSAC" and not is_filter_loop_locked(state):
            health |= 0x1000

        return f"0x{health:X}"

    return handler


def make_sync_hold_dur_handler(state: DeviceState):
    """
    SYNC:HOLD:DUR? -- GERCEK cihazin kilavuzuna gore bu TEK sayi
    degil, IKI sayi donduruyor:
      1. Holdover suresi (saniye) -- holdover'daysa GUNCEL sure,
         degilse EN SON holdover'in suresi.
      2. Holdover durumu: 1 = su an holdoverda, 0 = degil.

    DEGISTI: eskiden holdover disinda her zaman "0,0" donuyorduk.
    Kilavuz §3.6.1 bunun aksini soyluyor: "If the Receiver is not in
    holdover, the response quantifies the PREVIOUS holdover." Artik
    biten holdover'in suresi state.last_holdover_duration_seconds
    icinde saklaniyor (bkz. device_state.exit_holdover) ve burada
    donduruluyor. Hic holdover yasanmamissa "0,0" dogru cevaptir.
    """

    def handler() -> str:
        if state.holdover and state.holdover_started_at is not None:
            elapsed_seconds = (
                datetime.now() - state.holdover_started_at
            ).total_seconds()
            return f"{elapsed_seconds:.1f},1"

        if state.last_holdover_duration_seconds is None:
            return "0,0"

        return f"{state.last_holdover_duration_seconds:.1f},0"

    return handler


def make_sync_hold_init_setter(state: DeviceState):
    """
    SYNC:HOLD:INIT -- holdover'i BASLATAN setter komutu.
    Deger almaz ("_" ile isaretledik -- Python'da "bu parametreyi
    kasitli olarak kullanmiyorum" demenin yaygin yolu budur).
    """

    def setter(_value: str) -> Optional[str]:
        # Hazirligi device_state.enter_holdover() yapiyor: hem
        # config_loader hem bu komut AYNI fonksiyonu cagirsin diye.
        # Giriste TINT donduruluyor (modeldeki x0).
        enter_holdover(state)
        return None

    return setter


def make_sync_hold_rec_init_setter(state: DeviceState):
    """
    SYNC:HOLD:REC:INIT -- holdover'dan CIKISI (recovery) baslatan
    setter. Basitlestirilmis varsayimimiz: bu komut geldiginde cihaz
    aninda tekrar kilitlenmis kabul ediliyor.
    """

    def setter(_value: str) -> Optional[str]:
        # exit_holdover() ayrica biten holdover'in SURESINI saklar,
        # boylece SYNC:HOLD:DUR? sonrasinda "onceki holdover"i
        # dondurebilir (kilavuz §3.6.1).
        exit_holdover(state)
        return None

    return setter


def make_sync_source_mode_setter(state: DeviceState):
    """
    SYNC:SOUR:MODE <deger> -- senkronizasyon kaynak modunu degistirir.
    Ornek kullanim: "SYNC:SOUR:MODE GPS"
    """

    def setter(value: str) -> Optional[str]:
        if value:
            state.sync_source_mode = value
        return None

    return setter


def register_sync_commands(parser: SCPIParser, state: DeviceState) -> None:
    """Bu dosyadaki tum SYNC komutlarini (query + setter) parser'a kaydeder."""
    parser.register("SYNC?", make_sync_handler(state))
    parser.register("SYNC:LOCKED?", make_sync_locked_handler(state))
    parser.register("SYNC:TINT?", make_sync_tint_handler(state))
    parser.register("SYNC:HEALTH?", make_sync_health_handler(state))
    parser.register("SYNC:HOLD:DUR?", make_sync_hold_dur_handler(state))
    parser.register("SYNC:HOLD:STATE?", make_sync_hold_state_handler(state))
    parser.register("SYNC:FEE?", make_sync_fee_handler(state))
    parser.register("SYNC:SOUR:STATE?", make_sync_source_state_handler(state))
    parser.register("SYNC:TINT:CSAC?", make_sync_tint_csac_handler(state))
    parser.register("SYNC:TINT:FILTER?", make_sync_tint_filter_handler(state))
    parser.register("SYNC:TINT:THRESHOLD?", make_sync_tint_threshold_handler(state))
    parser.register("SYNC:OUT:FILTER?", make_sync_out_filter_handler(state))
    parser.register("SYNC:OUT:1PPS:RESET?", make_sync_out_1pps_reset_handler(state))
    parser.register("SYNC:OUT:1PPS:DOMAIN?", make_sync_out_1pps_domain_handler(state))

    parser.register_setter("SYNC:HOLD:INIT", make_sync_hold_init_setter(state))
    parser.register_setter("SYNC:HOLD:REC:INIT", make_sync_hold_rec_init_setter(state))
    parser.register_setter("SYNC:SOUR:MODE", make_sync_source_mode_setter(state))

    # --- KISA/UZUN FORM ALIAS'LARI (gercek kilavuzdan) ---
    # Kilavuz: "SYNChronization:HOLDover:DURation?" -> mandatory
    # SYNC+HOLD+DUR (zaten bizim canonical'imizle ayni), long alias:
    parser.register_alias("SYNCHRONIZATION:HOLDOVER:DURATION?", "SYNC:HOLD:DUR?")
    parser.register_alias("SYNCHRONIZATION:HOLDOVER:INITIATE", "SYNC:HOLD:INIT")
    parser.register_alias(
        "SYNCHRONIZATION:HOLDOVER:RECOVERY:INITIATE", "SYNC:HOLD:REC:INIT"
    )
    parser.register_alias("SYNCHRONIZATION:SOURCE:MODE", "SYNC:SOUR:MODE")
    parser.register_alias("SYNCHRONIZATION:TINTERVAL?", "SYNC:TINT?")
    parser.register_alias("SYNCHRONIZATION?", "SYNC?")
    parser.register_alias("SYNCHRONIZATION:HOLDOVER:STATE?", "SYNC:HOLD:STATE?")
    parser.register_alias("SYNCHRONIZATION:FEESTIMATE?", "SYNC:FEE?")
    parser.register_alias("SYNC:FEEST?", "SYNC:FEE?")
    parser.register_alias("SYNCHRONIZATION:SOURCE:STATE?", "SYNC:SOUR:STATE?")
    parser.register_alias("SYNCHRONIZATION:TINTERVAL:CSAC?", "SYNC:TINT:CSAC?")
    parser.register_alias("SYNCHRONIZATION:TINTERVAL:FILTER?", "SYNC:TINT:FILTER?")
    parser.register_alias(
        "SYNCHRONIZATION:TINTERVAL:THRESHOLD?", "SYNC:TINT:THRESHOLD?"
    )
    parser.register_alias("SYNCHRONIZATION:OUTPUT:FILTER?", "SYNC:OUT:FILTER?")
    parser.register_alias(
        "SYNCHRONIZATION:OUTPUT:1PPS:RESET?", "SYNC:OUT:1PPS:RESET?"
    )
    parser.register_alias(
        "SYNCHRONIZATION:OUTPUT:1PPS:DOMAIN?", "SYNC:OUT:1PPS:DOMAIN?"
    )

    # Bunlarda canonical'imiz zaten UZUN yazim (gorev PDF'i oyle
    # istemisti: "LOCKED", "HEALTH"), o yuzden kilavuzun KISA formunu
    # alias olarak ekliyoruz (ters yon):
    parser.register_alias("SYNC:LOCK?", "SYNC:LOCKED?")
    parser.register_alias("SYNCHRONIZATION:LOCKED?", "SYNC:LOCKED?")
    parser.register_alias("SYNC:HEA?", "SYNC:HEALTH?")
    parser.register_alias("SYNCHRONIZATION:HEALTH?", "SYNC:HEALTH?")

def make_sync_fee_handler(state: DeviceState):
    """
    SYNChronization:FEEstimate? -- frekans hata tahmini (§3.6.10).

    Kilavuz: "similar to the Allan Variance using a 1000s measurement
    interval". Dolayisiyla SABIT DEGILDIR -- gercek cihazin uc ardisik
    sorgusu 1.31E-11, 2.49E-11 ve 1.59E-11 vermisti.

    Bu deger ayni zamanda holdover hata birikiminin HIZINI belirler
    (models/holdover.py'deki y0). Yani kullanici bunu okuyup, GPS
    kaybolursa hatanin ne hizla buyuyecegini kendisi hesaplayabilir.
    """

    def handler() -> str:
        return f"{measured_freq_error_estimate(state):.2E}"

    return handler


def make_sync_hold_state_handler(state: DeviceState):
    """
    SYNChronization:HOLDover:STATe? -- holdover'da miyiz? (1/0)

    SYNC:HOLD:DUR? de ayni bilgiyi ikinci alaninda veriyor; bu, onu
    tek basina sormanin yolu.
    """

    def handler() -> str:
        return "1" if state.holdover else "0"

    return handler


def make_sync_source_state_handler(state: DeviceState):
    """SYNChronization:SOURce:STATE? -- aktif 1PPS kaynagi (§3.6.5)."""

    def handler() -> str:
        return state.sync_source_state

    return handler


def make_sync_tint_csac_handler(state: DeviceState):
    """
    SYNChronization:TINTerval:CSAC? -- Rubidyum 1PPS ile GNSS/harici
    1PPS arasindaki zaman farki (§3.6.7).

    Bu, bizim ana TINT modelimizin ta kendisi: holdover'da biriken
    hatayi gosteren deger budur. Kilavuz §3.6.2 bu komutu ozellikle
    "GPS'e kilitli degilken Rubidyum osilatorun kaymasini gormek"
    icin isaret ediyor.
    """

    def handler() -> str:
        return f"{_tint_seconds(state):.3E}"

    return handler


def make_sync_tint_filter_handler(state: DeviceState):
    """
    SYNChronization:TINTerval:FILTer? -- FILTRE osilator 1PPS'i ile
    RUBIDYUM 1PPS'i arasindaki fark (§3.6.8).

    DIKKAT -- BU FARKLI BIR OLCUM: ana TINT, Rubidyum'u GNSS'e
    kiyaslar; bu ise filtre OCXO'sunu Rubidyum'a kiyaslar. Ikisi ayri
    dongulerdir.

    Bu yuzden HOLDOVER'DA BIRIKMEZ: GNSS kaybolsa da filtre dongusu
    Rubidyum'a kilitli kalir (kilavuz §2.5). Genligi de daha kucuktur
    -- §1.1'e gore filtre osilatorunun faz dogrulugu 0.3 ns
    mertebesinde, Rubidyum'un GNSS'e gore 0.2 ns'i ile ayni mertebede
    ama ayri bir olcum.
    """

    def handler() -> str:
        return f"{filter_tint_seconds(state):.3E}"

    return handler


def make_sync_tint_threshold_handler(state: DeviceState):
    """
    SYNChronization:TINTerval:THReshold? -- jam-sync esigi, ns (§3.6.19).

    Faz farki bu esigi asarsa cihaz "jam-sync" yapip fazi zorla
    hizalar. Gecerli aralik [50, 2000], varsayilan 220.
    """

    def handler() -> str:
        return str(state.tint_threshold_ns)

    return handler


def make_sync_out_filter_handler(state: DeviceState):
    """SYNChronization:OUTput:FILTer? -- faz gurultu filtresi (§3.6.17)."""

    def handler() -> str:
        return "ON" if state.phase_noise_filter_enabled else "OFF"

    return handler


def make_sync_out_1pps_reset_handler(state: DeviceState):
    """SYNChronization:OUTput:1PPs:RESET? -- reset'te 1PPS (§3.6.13)."""

    def handler() -> str:
        return "ON" if state.pps_reset_enabled else "OFF"

    return handler


def make_sync_out_1pps_domain_handler(state: DeviceState):
    """
    SYNChronization:OUTput:1PPS:DOMAIN? -- 1PPS cikisi hangi
    osilatordan aliniyor: CSAC (Rubidyum) mu, FILTer (OCXO) mu (§3.6.15).
    """

    def handler() -> str:
        return state.pps_domain

    return handler
