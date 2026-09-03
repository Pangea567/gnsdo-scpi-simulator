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

from gnsdo_simulator.device_state import DeviceState, is_locked
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
            f"FREQ ERROR ESTIMATE : {state.freq_error_estimate:.2E}",
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
    TINT (time interval error) degerini SANIYE cinsinden sayisal
    olarak hesaplar -- hem SYNC:TINT? cevabini metne cevirmek hem de
    SYNC:HEALTH?'in "faz farki > 210ns mi" kontrolu icin kullanilir.
    Boylece iki yerde ayni sabitleri tekrar yazmiyoruz.
    """
    if state.holdover:
        return 0.000000850  # holdover'da hata payi biraz daha buyuk (sabit varsayim)
    return 0.000000012  # normal calismada kucuk, sabit bir deger (varsayim)


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

        0x4    faz farki (TINT) > 210ns
        0x8    calisma suresi < 200 saniye (yeni acilmis)
        0x10   holdover suresi > 60 saniye
        0x400  donanim/osilator arizasi (hardware_fault)

    0x0 = "duzgun kilitli ve isinmis, tamamen saglikli" (kilavuzun
    kendi tanimi).
    """

    def handler() -> str:
        health = 0

        if _tint_seconds(state) > 210e-9:
            health |= 0x4

        runtime_seconds = (datetime.now() - state.process_started_at).total_seconds()
        if runtime_seconds < 200:
            health |= 0x8

        if state.holdover and state.holdover_started_at is not None:
            holdover_seconds = (datetime.now() - state.holdover_started_at).total_seconds()
            if holdover_seconds > 60:
                health |= 0x10

        if state.hardware_fault:
            health |= 0x400

        return f"0x{health:X}"

    return handler


def make_sync_hold_dur_handler(state: DeviceState):
    """
    SYNC:HOLD:DUR? -- GERCEK cihazin kilavuzuna gore bu TEK sayi
    degil, IKI sayi donduruyor:
      1. Holdover suresi (saniye) -- holdover'daysa GUNCEL sure,
         degilse EN SON holdover'in suresi.
      2. Holdover durumu: 1 = su an holdoverda, 0 = degil.

    Biz "en son holdover'in suresini" ayrica saklamiyoruz (MVP
    basitlestirmesi) -- holdover'da degilken "0,0" donuyoruz.
    """

    def handler() -> str:
        if not state.holdover or state.holdover_started_at is None:
            return "0,0"
        elapsed_seconds = (datetime.now() - state.holdover_started_at).total_seconds()
        return f"{elapsed_seconds:.1f},1"

    return handler


def make_sync_hold_init_setter(state: DeviceState):
    """
    SYNC:HOLD:INIT -- holdover'i BASLATAN setter komutu.
    Deger almaz ("_" ile isaretledik -- Python'da "bu parametreyi
    kasitli olarak kullanmiyorum" demenin yaygin yolu budur).
    """

    def setter(_value: str) -> Optional[str]:
        state.holdover = True
        state.sync_locked = False
        state.holdover_started_at = datetime.now()
        return None

    return setter


def make_sync_hold_rec_init_setter(state: DeviceState):
    """
    SYNC:HOLD:REC:INIT -- holdover'dan CIKISI (recovery) baslatan
    setter. Basitlestirilmis varsayimimiz: bu komut geldiginde cihaz
    aninda tekrar kilitlenmis kabul ediliyor.
    """

    def setter(_value: str) -> Optional[str]:
        state.holdover = False
        state.sync_locked = True
        state.holdover_started_at = None
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

    # Bunlarda canonical'imiz zaten UZUN yazim (gorev PDF'i oyle
    # istemisti: "LOCKED", "HEALTH"), o yuzden kilavuzun KISA formunu
    # alias olarak ekliyoruz (ters yon):
    parser.register_alias("SYNC:LOCK?", "SYNC:LOCKED?")
    parser.register_alias("SYNCHRONIZATION:LOCKED?", "SYNC:LOCKED?")
    parser.register_alias("SYNC:HEA?", "SYNC:HEALTH?")
    parser.register_alias("SYNCHRONIZATION:HEALTH?", "SYNC:HEALTH?")