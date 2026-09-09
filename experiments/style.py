"""
experiments/style.py

Tum bildiri sekilleri icin ORTAK matplotlib stili.

Amac: her sekil ayni tipografi ve olculerle ciksin, bildiride tutarli
gorunsunler. Ciktilar VEKTOR PDF (LaTeX'e \\includegraphics ile temiz
girer) ve ayrica hizli onizleme icin PNG.

Not: sistemde LaTeX (pdflatex) kurulu OLMAYABILIR, o yuzden usetex
KULLANMIYORUZ; matplotlib'in kendi mathtext'i + serif fontu ile IEEE
konferans gorunumune yakin, tasinabilir bir sonuc uretiyoruz.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # ekran gerektirmeyen dosya-cikti arka ucu
import matplotlib.pyplot as plt

FIGDIR = Path(__file__).parent / "figures"
FIGDIR.mkdir(exist_ok=True)

# IEEE tek-sutun genisligi ~3.5 inc; cift-sutun ~7.16 inc
COL_WIDTH = 3.5
COL2_WIDTH = 7.16

# Renk korlugune ve gri-tonlu baskiya dayanikli, sade bir palet
COLORS = {
    "model": "#1f4e79",   # koyu mavi -- model/ana egri
    "real": "#c0392b",    # kirmizi -- gercek cihaz olcumleri
    "old": "#7f8c8d",     # gri -- eski (statik) davranis
    "accent": "#e67e22",  # turuncu -- esik/vurgu
    "band": "#aed6f1",    # acik mavi -- belirsizlik/aralik bandi
}


def apply_style():
    """Ortak rcParams'i uygular. Her sekil script'i basta bunu cagirir."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif"],
        "mathtext.fontset": "dejavuserif",
        "font.size": 9,
        "axes.titlesize": 9,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.linewidth": 0.6,
        "grid.linewidth": 0.4,
        "lines.linewidth": 1.3,
        "grid.alpha": 0.35,
        "axes.grid": True,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "legend.frameon": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def save(fig, name):
    """
    Sekli hem PDF (bildiri icin) hem PNG (onizleme icin) olarak kaydeder.
    Dosya adi uzantisiz verilir: save(fig, "fig01_warmup").
    """
    for ext in ("pdf", "png"):
        out = FIGDIR / f"{name}.{ext}"
        fig.savefig(out)
    plt.close(fig)
    return FIGDIR / f"{name}.pdf"
