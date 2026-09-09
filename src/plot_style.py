"""
plot_style.py

Projedeki TUM matplotlib grafiklerini IEEE konferans bildirisi
kalitesinde ve BIRBIRIYLE TUTARLI gostermek icin ortak stil modulu.

Kullanim:
    import plot_style
    plot_style.apply_ieee_style()
    fig, ax = plt.subplots(figsize=plot_style.SINGLE_COL)
    ...
    plot_style.save(fig, "fig01_isim")   # figures/ altina PDF + PNG

Neden src/ altinda: deney script'leri zaten src'yi yola ekliyor
(gnsdo_simulator'i import edebilmek icin), boylece `import plot_style`
hicbir ek ayar gerektirmeden calisir.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # dosyaya yazan, ekran gerektirmeyen arka uc
import matplotlib.pyplot as plt
from cycler import cycler

# --- Figur olculeri (inc) ---
SINGLE_COL = (3.5, 2.5)    # IEEE tek sutun
DOUBLE_COL = (7.16, 3.5)   # IEEE cift sutun

# --- Okabe-Ito renk-korlugune duyarli palet (STANDART SIRA) ---
# Kaynak: Okabe & Ito (2008). Tum grafiklerde AYNI sirayla kullanilir,
# boylece "ilk seri" her sekilde ayni renk olur -> tutarlilik.
OKABE_ITO = [
    "#000000",  # siyah
    "#E69F00",  # turuncu
    "#56B4E9",  # gok mavisi
    "#009E73",  # yesil
    "#F0E442",  # sari
    "#0072B2",  # mavi
    "#D55E00",  # kiremit
    "#CC79A7",  # mor
]

# Sik kullanilan roller icin adlandirilmis kisayollar (paletten secili)
C_MODEL = OKABE_ITO[5]    # mavi   -- model / ana egri
C_REAL = OKABE_ITO[6]     # kiremit -- gercek cihaz olcumleri
C_OLD = OKABE_ITO[0]      # siyah  -- eski/statik davranis
C_ACCENT = OKABE_ITO[1]   # turuncu -- esik / vurgu
C_ALT = OKABE_ITO[3]      # yesil  -- ikincil egri

FIGDIR = Path(__file__).resolve().parent.parent / "experiments" / "figures"


def apply_ieee_style():
    """IEEE konferans gorunumu icin ortak rcParams'i uygular."""
    plt.rcParams.update({
        # tipografi -- Computer Modern (LaTeX gorunumu), tasinabilir
        "mathtext.fontset": "cm",
        "font.family": "serif",
        "font.size": 8,
        "axes.titlesize": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 8,          # eksen fontuyla ayni boy

        # figur / kayit
        "figure.figsize": SINGLE_COL,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.format": "pdf",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,

        # eksenler
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.8,
        "axes.prop_cycle": cycler(color=OKABE_ITO),

        # izgara
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
        "grid.linewidth": 0.5,

        # gosterge (legend)
        "legend.frameon": False,

        # cizgiler
        "lines.linewidth": 1.4,
    })


def save(fig, name):
    """
    Sekli hem PDF (LaTeX'e gomulmek icin) hem PNG (hizli onizleme)
    olarak experiments/figures/ altina kaydeder. Ad uzantisiz verilir.
    """
    FIGDIR.mkdir(parents=True, exist_ok=True)
    pdf = FIGDIR / f"{name}.pdf"
    fig.savefig(pdf)
    fig.savefig(FIGDIR / f"{name}.png", dpi=200)
    plt.close(fig)
    return pdf
