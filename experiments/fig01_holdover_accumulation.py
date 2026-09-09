"""
fig01: Holdover'da TINT hata birikimi ve kuadratik terimin katkisi.

x(t) = x0 + y0*t + (D/2)t^2. Tam model ile "yalniz dogrusal" (y0*t)
arasindaki golgeli alan = yaslanma (kuadratik) katkisi. Saatler
mertebesinde gorunmez, gunler mertebesinde belirginlesir.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
import matplotlib.pyplot as plt
import plot_style as ps
from _reference import HEALTH_PHASE_THRESHOLD_NS
from gnsdo_simulator.models.holdover import holdover_tint_seconds

FEE = 1.8e-11

def main():
    ps.apply_ieee_style()
    t = np.linspace(0, 24 * 3600, 600)
    saat = t / 3600
    full = np.array([holdover_tint_seconds(ti, 0.0, FEE) for ti in t]) * 1e9
    lin = FEE * t * 1e9

    fig, ax = plt.subplots(figsize=ps.SINGLE_COL)
    ax.fill_between(saat, lin, full, color=ps.C_ACCENT, alpha=0.25,
                    label="kuadratik (yaslanma) katkisi")
    ax.plot(saat, full, color=ps.C_MODEL, label=r"tam model $x(t)$")
    ax.plot(saat, lin, color=ps.C_OLD, ls="--", lw=1.0,
            label=r"yaln. dogrusal $y_0\,t$")

    ax.axhline(HEALTH_PHASE_THRESHOLD_NS, color=ps.C_REAL, lw=0.9, ls=":")
    t_cross = HEALTH_PHASE_THRESHOLD_NS * 1e-9 / FEE / 3600
    ax.annotate("HEALTH 0x4\n(210 ns)", xy=(t_cross, HEALTH_PHASE_THRESHOLD_NS),
                xytext=(t_cross + 1.5, HEALTH_PHASE_THRESHOLD_NS + 180),
                color=ps.C_REAL, fontsize=7,
                arrowprops=dict(arrowstyle="->", color=ps.C_REAL, lw=0.7))

    ax.set_xlabel("holdover suresi (saat)")
    ax.set_ylabel("TINT (ns)")
    ax.set_xlim(0, 24)
    ax.set_ylim(0, full.max() * 1.05)
    ax.legend(loc="upper left")
    print("yazildi:", ps.save(fig, "fig01_holdover_accumulation"))

if __name__ == "__main__":
    main()
