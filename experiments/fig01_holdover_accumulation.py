"""
fig01: Holdover'da TINT hata birikimi.

Gosterdigi: GPS kaybolunca zaman hatasinin x(t)=x0+y0*t+(D/2)t^2 ile
buyumesi. Dogrusal bolge (saatler) ve kuadratik terimin belirginlestigi
bolge (gunler) ayrilir; kilavuz esikleri (§3.6.18 210ns, §3.6.19 220ns)
isaretlenir.

Bu bir MODEL ILLUSTRASYONUDUR -- cihazin dinamik davranisini gosterir.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
from style import apply_style, save, COLORS, COL_WIDTH
from _reference import HEALTH_PHASE_THRESHOLD_NS, TINT_JAMSYNC_THRESHOLD_NS
import matplotlib.pyplot as plt

from gnsdo_simulator.models.holdover import holdover_tint_seconds

FEE = 1.8e-11  # cihaz kayitlarindaki uc olcumun ortalamasi (y0)

def main():
    apply_style()
    t = np.linspace(0, 12 * 3600, 500)  # 12 saat
    tint_ns = np.array([holdover_tint_seconds(ti, 0.0, FEE) for ti in t]) * 1e9
    # yalniz dogrusal terim (kuadratigi ayirt etmek icin)
    linear_ns = FEE * t * 1e9

    fig, ax = plt.subplots(figsize=(COL_WIDTH, 2.5))
    saat = t / 3600
    ax.plot(saat, tint_ns, color=COLORS["model"], label=r"tam model $x(t)$")
    ax.plot(saat, linear_ns, color=COLORS["old"], ls="--", lw=1.0,
            label=r"yaln. dogrusal $y_0 t$")

    ax.axhline(HEALTH_PHASE_THRESHOLD_NS, color=COLORS["accent"], lw=0.9, ls=":")
    ax.text(0.15, HEALTH_PHASE_THRESHOLD_NS + 8, "HEALTH 0x4 (210 ns)",
            color=COLORS["accent"], fontsize=7)

    # 210 ns'ye ulasma ani
    t_cross = HEALTH_PHASE_THRESHOLD_NS * 1e-9 / FEE / 3600
    ax.axvline(t_cross, color=COLORS["accent"], lw=0.6, ls=":", alpha=0.6)
    ax.text(t_cross + 0.15, 40, f"{t_cross:.1f} sa", color=COLORS["accent"],
            fontsize=7, rotation=90, va="bottom")

    ax.set_xlabel("holdover suresi (saat)")
    ax.set_ylabel("TINT (ns)")
    ax.set_xlim(0, 12)
    ax.set_ylim(0, tint_ns.max() * 1.05)
    ax.legend(loc="upper left")
    out = save(fig, "fig01_holdover_accumulation")
    print("yazildi:", out)

if __name__ == "__main__":
    main()
