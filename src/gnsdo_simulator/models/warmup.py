"""
models/warmup.py

ISINMA (WARMUP) MODELI ve SERVO DURUM MAKINESI.

PROBLEM:
  Cihaz fise takildigi anda calismaya hazir degildir. Icindeki atomik
  saat once isinmali, sonra GNSS'e kilitlenmeli. Bu sirada:
    - Sicakliklar ortam sicakligindan calisma sicakligina TIRMANIR
    - Cihaz bir dizi DURUMDAN gecer (isinma -> kilitleniyor -> kilitli)
  Simulatorumuz bu gecisi hic modellemiyordu: aciliste zaten sicak ve
  (2 dakika sonra) aniden kilitli oluyordu.

--------------------------------------------------------------------
1) ISIL RAMPA
--------------------------------------------------------------------

Cihaz 5W'tan fazla guc harcayip isinir (kilavuz §1.3.4). Isinan bir
cismin sicakligi ANI degil USTEL olarak yaklasir -- Newton'un soguma
yasasinin ayni fizigi, ters yonde:

    T(t) = T_son - (T_son - T_bas) * e^(-t/tau)

  T_bas : ortam sicakligi (cihaz henuz sogukken)
  T_son : kararli calisma sicakligi
  tau   : ISIL ZAMAN SABITI -- aradaki farkin ~%63'unun kapandigi sure

Nicin ustel? Cunku isi kaybi, cisimle ortam arasindaki SICAKLIK FARKI
ile orantilidir. Fark buyukken hizli isinir, fark kapandikca yavaslar.
Dogrusal bir rampa fiziksel olarak yanlis olurdu: sicaklik hedefe
varinca aniden durmaz, ona asimptotik yaklasir.

Pratik olarak 3*tau sonunda farkin %95'i, 5*tau sonunda %99'u kapanir.

--------------------------------------------------------------------
2) SERVO DURUM MAKINESI
--------------------------------------------------------------------

Kilavuz §3.10.3, SERVo:STATe? sorgusunun donduregi degerleri
tanimliyor:

    0  Rubidyum/filtre osilator ISINMASI
    1  Holdover
    2  KILITLENIYOR (Rubidyum/filtre egitimi)
    4  (tanimsiz)
    5  Holdover ama HALEN FAZ KILITLI
       -- GNSS kaybindan sonra ~100 saniye bu durumda kalir
    6  Kilitli, GNSS aktif

Zaman esikleri de kilavuzdan:
    0 -> 2 : 120 saniye  (§1.1 "less than 2 minutes warmup time to
             atomic lock" -- atomik kilit saglandi, artik GNSS'e
             kilitlenme egitimi basliyor)
    2 -> 6 : 1200 saniye (§2.5 "will typically happen in less than
             20 minutes after power-on with a GNSS antenna connected")

DURUM 5 NICIN ONEMLI:
  GNSS sinyali kesildiginde cihaz aninda "holdover" demez. Faz halen
  kilitlidir ve bir sure oyle kalir (~100 s). Bu, gercek bir gecis
  davranisidir ve simulatorde olmamasi, GNSS kaybini izleyen bir test
  uygulamasinin gercek cihazda gorecegi ara durumu hic gormemesi
  anlamina gelirdi.

BU MODULUN KURALI:
  Fonksiyonlar SAFTIR -- datetime.now() cagirmaz, gecen sureyi
  PARAMETRE olarak alir. Boylece "20 dakika gecmis olsaydi" sorusunu
  testte gercek zamanda beklemeden sorabiliriz.
"""

import math

# --- SERVo:STATe? degerleri (kilavuz §3.10.3) ---
SERVO_STATE_WARMUP = 0
SERVO_STATE_HOLDOVER = 1
SERVO_STATE_LOCKING = 2
SERVO_STATE_HOLDOVER_PHASE_LOCKED = 5
SERVO_STATE_LOCKED = 6

# Kilavuz §1.1: "less than 2 minutes warmup time to atomic lock".
# Bu sure dolunca atomik kilit saglanmis sayilir ve cihaz GNSS'e
# kilitlenme egitimine (durum 2) gecer.
ATOMIC_LOCK_SECONDS = 120.0

# Kilavuz §2.5: kilit gostergesi "typically ... in less than 20
# minutes after power-on with a GNSS antenna connected".
GNSS_LOCK_SECONDS = 1200.0

# Kilavuz §3.10.3, durum 5 aciklamasi: "stays in this state for about
# 100s after GNSS lock is lost".
HOLDOVER_PHASE_LOCKED_SECONDS = 100.0

# Isil zaman sabiti (saniye). Cihazin kararli sicakliga yaklasma hizi.
#
# DUZELTILDI (cihazi calistiran kisinin gozlemi): sicaklik HIZLI yukselir
# -- birkac dakikada 40-50 C'ye ulasir. Eski deger (600 s) yanlisti;
# kilavuzun 20 DAKIKALIK KILIT suresinden secilmisti, ama o GNSS'e
# kilitlenme suresidir, SICAKLIK degil. Kilavuz §1.1 de bunu dogruluyor:
# "less than 2 minutes warmup time to atomic lock" -- atomik paket 2
# dakikada calisma sicakligina ulasir, yani isinma hizlidir.
#
# 90 s ile: 1 dk'da ~38 C, 2 dk'da ~46 C, 3 dk'da ~49 C, 5 dk'da ~52 C.
# Isinma (hizli, ~dakikalar) ile GNSS kilidi (yavas, ~20 dk) AYRI
# sureclerdir; ikincisi servo durum makinesinde ayrica tutulur.
THERMAL_TIME_CONSTANT_SECONDS = 90.0

# Cihazin acilis anindaki ortam sicakligi varsayimi (C).
# VARSAYIM: kilavuz ortam sicakligi vermiyor, gercek cihaz kayitlari
# da acilis anini icermiyor. Ic mekan kullanimi icin makul bir deger
# secildi (kilavuz §1.3.4 cihazin ic mekan icin tasarlandigini soyler).
# Config'ten degistirilebilir.
AMBIENT_TEMPERATURE_C = 25.0


def thermal_ramp(
    elapsed_seconds: float,
    final_temperature: float,
    start_temperature: float = AMBIENT_TEMPERATURE_C,
    time_constant: float = THERMAL_TIME_CONSTANT_SECONDS,
) -> float:
    """
    Isinan bir yuzeyin sicakligini USTEL yaklasimla hesaplar:

        T(t) = T_son - (T_son - T_bas) * e^(-t/tau)

    t <= 0 icin baslangic sicakligi donulur.

    Nicin ustel de dogrusal degil: isi kaybi sicaklik FARKI ile
    orantilidir. Fark buyukken hizli isinir, fark kapandikca yavaslar.
    Dogrusal rampada sicaklik hedefe varip aniden dururdu -- gercekte
    asimptotik yaklasir.
    """
    if elapsed_seconds <= 0:
        return start_temperature

    fark = final_temperature - start_temperature
    return final_temperature - fark * math.exp(-elapsed_seconds / time_constant)


def servo_state(
    elapsed_seconds: float,
    holdover: bool = False,
    holdover_elapsed_seconds: float = 0.0,
    gnss_locked: bool = True,
) -> int:
    """
    SERVo:STATe? degerini hesaplar (kilavuz §3.10.3).

    Oncelik sirasi (ilk uyan kazanir):

      1. HOLDOVER: GNSS kaybindan sonraki ilk ~100 saniye faz halen
         kilitlidir (durum 5), sonrasinda tam holdover (durum 1).
         Bu ara durum gercek bir gecis davranisidir.

      2. ISINMA: aciliskan itibaren 120 saniye gecmeden atomik kilit
         yoktur (durum 0).

      3. KILITLENIYOR: atomik kilit var ama GNSS'e kilitlenme egitimi
         surmekte, ya da GNSS fix'i yok (durum 2).

      4. KILITLI: her sey tamam (durum 6).
    """
    if holdover:
        if holdover_elapsed_seconds < HOLDOVER_PHASE_LOCKED_SECONDS:
            return SERVO_STATE_HOLDOVER_PHASE_LOCKED
        return SERVO_STATE_HOLDOVER

    if elapsed_seconds < ATOMIC_LOCK_SECONDS:
        return SERVO_STATE_WARMUP

    if not gnss_locked or elapsed_seconds < GNSS_LOCK_SECONDS:
        return SERVO_STATE_LOCKING

    return SERVO_STATE_LOCKED


def is_warming_up(elapsed_seconds: float) -> bool:
    """Cihaz halen isinma (durum 0) asamasinda mi?"""
    return elapsed_seconds < ATOMIC_LOCK_SECONDS
