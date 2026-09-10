"""Plot 08: SYNC:HEALTH? bit activity during holdover -- clean timeline."""
import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt, plot_style as ps
from harness import read_csv

def main():
    ps.apply_ieee_style()
    d = read_csv("health_bits")
    saat = np.array([r["saat"] for r in d])
    b10 = np.array([r["bit10_holdover"] for r in d])
    b4  = np.array([r["bit4_faz"] for r in d])
    tmax = saat.max()
    def onset(bits):
        idx = np.argmax(bits > 0)
        return saat[idx] if bits.any() else None
    t10, t4 = onset(b10), onset(b4)

    fig, ax = plt.subplots(figsize=(ps.SINGLE_COL[0], 1.9), constrained_layout=True)
    # iki serit: alt=0x4, ust=0x10
    ax.broken_barh([(t10, tmax - t10)], (1.0, 0.55), facecolors=ps.C_MODEL, alpha=0.85)
    ax.broken_barh([(t4,  tmax - t4)],  (0.1, 0.55), facecolors=ps.C_REAL, alpha=0.85)

    ax.set_yticks([0.375, 1.275])
    ax.set_yticklabels(["0x4\nphase > 210 ns", "0x10\nholdover > 60 s"], fontsize=7)

    # birlesim ani
    ax.axvline(t4, color=ps.C_OLD, ls=":", lw=0.8)
    ax.annotate("combined 0x14", xy=(t4, 1.85), xytext=(t4 + 0.15, 1.9),
                fontsize=7, color=ps.C_OLD, va="top")
    ax.text(t4/2, 1.95, "0x10", fontsize=7, color=ps.C_MODEL, ha="center", va="top")

    ax.set_xlabel("holdover duration (hours)")
    ax.set_xlim(0, tmax); ax.set_ylim(0, 2.1)
    ax.spines["left"].set_visible(False); ax.tick_params(left=False)
    print("written:", ps.save(fig, "fig08_health_bits"))

if __name__ == "__main__": main()
