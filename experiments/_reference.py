"""
experiments/_reference.py

GERCEK CIHAZ REFERANS DEGERLERI -- tek kaynak.

Buradaki her sayi docs/gercek-cihaz-ciktilari.md dosyasindaki ham
kayittan alinmistir. Sekil script'leri bu degerleri BURADAN okur,
boylece her sekil ayni gercek veriyi kullanir ve bir yerde
duzeltirsek hepsi guncellenir.

ONEMLI DURUSTLUK NOTU: Bu olcumler CIHAZ CALISIRKEN RASTGELE ANLARDA
alindi; ZAMAN DAMGALARI YOK. Bu yuzden onlari isinma egrisinde belirli
bir x (zaman) noktasina koYAMAYIZ. Dogru kullanim: gozlenen ARALIGI
ve DEGISKENLER ARASI ILISKILERI (PCB<->CSAC, EFC abs<->rel) gostermek.
"""

# MEAS? ciftleri: (PCB sicakligi, CSAC sicakligi) -- Celsius
# Kaynak: docs/gercek-cihaz-ciktilari.md, dort ardisik MEAS? sorgusu
MEAS_PAIRS = [
    (46.5688, 47.83),
    (52.7762, 54.10),
    (52.8652, 54.17),
    (49.7419, 51.13),
]

# DIAG? ciftleri: (EFControl Relative %, EFControl Absolute ppt)
EFC_PAIRS = [
    (-0.410000, -82),
    (-0.440000, -88),
    (-0.640000, -128),
    (-0.105000, -21),
]

# SYNC? uc ardisik sorgudan: FEE (frekans hata tahmini) ve TINT (s)
FEE_SAMPLES = [1.31e-11, 2.49e-11, 1.59e-11]
TINT_SAMPLES = [1.133e-08, -7.873e-09, -1.179e-08, 9.063e-09, 2.672e-09]

# Kilavuzdan turetilen sabitler (dogrulama hedefleri)
HEALTH_PHASE_THRESHOLD_NS = 210.0   # §3.6.18, HEALTH 0x4
TINT_JAMSYNC_THRESHOLD_NS = 220.0   # §3.6.19, varsayilan
PCB_OBSERVED_MIN = min(p for p, _ in MEAS_PAIRS)
PCB_OBSERVED_MAX = max(p for p, _ in MEAS_PAIRS)
CSAC_OBSERVED_MIN = min(c for _, c in MEAS_PAIRS)
CSAC_OBSERVED_MAX = max(c for _, c in MEAS_PAIRS)
