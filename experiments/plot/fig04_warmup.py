import os, sys
HERE=os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt
import plot_style as ps
from harness import read_csv
from _reference import PCB_OBSERVED_MIN, PCB_OBSERVED_MAX
from gnsdo_simulator.models.warmup import ATOMIC_LOCK_SECONDS, GNSS_LOCK_SECONDS

def main():
    ps.apply_ieee_style()
    d = read_csv("warmup")
    dk = np.array([r["dakika"] for r in d]); temp = np.array([r["pcb_c"] for r in d])
    a, g = ATOMIC_LOCK_SECONDS/60, GNSS_LOCK_SECONDS/60
    fig, ax = plt.subplots(figsize=ps.DOUBLE_COL)
    ax.axvspan(0, a, color=ps.OKABE_ITO[1], alpha=0.10)
    ax.axvspan(a, g, color=ps.OKABE_ITO[2], alpha=0.10)
    ax.axvspan(g, 60, color=ps.OKABE_ITO[3], alpha=0.10)
    for x,l in [(a/2,"durum 0\nisinma"),((a+g)/2,"durum 2\nkilitleniyor"),((g+60)/2,"durum 6\nkilitli")]:
        ax.text(x, 25.4, l, ha="center", va="bottom", fontsize=7, color=ps.C_OLD)
    ax.axhspan(PCB_OBSERVED_MIN, PCB_OBSERVED_MAX, color=ps.C_REAL, alpha=0.12)
    ax.text(59, (PCB_OBSERVED_MIN+PCB_OBSERVED_MAX)/2, "gozlenen\ngercek aralik",
            ha="right", va="center", fontsize=7, color=ps.C_REAL)
    ax.plot(dk, temp, color=ps.C_MODEL, label=r"PCB sicakligi $T(t)$ (model)")
    ax.axhline(52.8, color=ps.C_OLD, ls=":", lw=0.8)
    ax.axvline(g, color=ps.C_ALT, ls="--", lw=0.8)
    ax.annotate("SYNC:LOCKED? = 1", xy=(g,40), xytext=(g-13,33), fontsize=7,
                color=ps.C_ALT, arrowprops=dict(arrowstyle="->", color=ps.C_ALT, lw=0.7))
    ax.set_xlabel("acilistan itibaren gecen sure (dakika)")
    ax.set_ylabel("sicaklik ($^\\circ$C)")
    ax.set_xlim(0,60); ax.set_ylim(24,54); ax.legend(loc="lower right")
    print("yazildi:", ps.save(fig, "fig04_warmup_ramp"))

if __name__ == "__main__": main()
