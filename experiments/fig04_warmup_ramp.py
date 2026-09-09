"""
fig04: Soguk baslangicta isinma rampasi ve servo durum gecisleri.

Iki sey birden gosterir:
  - Sicakligin USTEL yaklasimla (dogrusal degil) kararli degere cikisi.
    T(t) = T_son - (T_son - T_bas) e^(-t/tau)
  - Arka planda servo durum bolgeleri: 0 isinma -> 2 kilitleniyor
    -> 6 kilitli. SYNC:LOCKED? yalnizca durum 6'da 1 olur.
  - Gozlenen gercek PCB araligi yatay bant olarak (zaman damgasi yok,
    bu yuzden bant; nokta degil).
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
import matplotlib.pyplot as plt
import plot_style as ps
from _reference import PCB_OBSERVED_MIN, PCB_OBSERVED_MAX
from gnsdo_simulator.models.warmup import (
    thermal_ramp, ATOMIC_LOCK_SECONDS, GNSS_LOCK_SECONDS,
    THERMAL_TIME_CONSTANT_SECONDS,
)

T_FINAL, T_AMBIENT = 52.8, 25.0

def main():
    ps.apply_ieee_style()
    t = np.linspace(0, 60 * 60, 600)
    dk = t / 60
    temp = np.array([thermal_ramp(ti, T_FINAL, T_AMBIENT,
                                  THERMAL_TIME_CONSTANT_SECONDS) for ti in t])

    fig, ax = plt.subplots(figsize=ps.DOUBLE_COL)

    # servo durum bolgeleri (arka plan)
    a_lock = ATOMIC_LOCK_SECONDS / 60
    g_lock = GNSS_LOCK_SECONDS / 60
    ax.axvspan(0, a_lock, color=ps.OKABE_ITO[1], alpha=0.10)
    ax.axvspan(a_lock, g_lock, color=ps.OKABE_ITO[2], alpha=0.10)
    ax.axvspan(g_lock, 60, color=ps.OKABE_ITO[3], alpha=0.10)
    for x, lbl in [(a_lock/2, "durum 0\nisinma"),
                   ((a_lock+g_lock)/2, "durum 2\nkilitleniyor"),
                   ((g_lock+60)/2, "durum 6\nkilitli")]:
        ax.text(x, 26, lbl, ha="center", va="bottom", fontsize=7, color=ps.C_OLD)

    # gozlenen gercek PCB araligi (bant)
    ax.axhspan(PCB_OBSERVED_MIN, PCB_OBSERVED_MAX, color=ps.C_REAL, alpha=0.12)
    ax.text(58, (PCB_OBSERVED_MIN + PCB_OBSERVED_MAX) / 2,
            "gozlenen\ngercek aralik", ha="right", va="center",
            fontsize=7, color=ps.C_REAL)

    ax.plot(dk, temp, color=ps.C_MODEL, label=r"PCB sicakligi $T(t)$ (model)")
    ax.axhline(T_FINAL, color=ps.C_OLD, ls=":", lw=0.8)
    ax.axvline(g_lock, color=ps.C_ALT, ls="--", lw=0.8)
    ax.annotate("SYNC:LOCKED? = 1", xy=(g_lock, 40),
                xytext=(g_lock - 12, 34), fontsize=7, color=ps.C_ALT,
                arrowprops=dict(arrowstyle="->", color=ps.C_ALT, lw=0.7))

    ax.set_xlabel("acilistan itibaren gecen sure (dakika)")
    ax.set_ylabel("sicaklik ($^\\circ$C)")
    ax.set_xlim(0, 60)
    ax.set_ylim(24, 54)
    ax.legend(loc="lower right")
    print("yazildi:", ps.save(fig, "fig04_warmup_ramp"))

if __name__ == "__main__":
    main()
