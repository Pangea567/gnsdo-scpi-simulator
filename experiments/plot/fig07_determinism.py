import os, sys
HERE=os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt
import plot_style as ps
from harness import read_csv

def main():
    ps.apply_ieee_style()
    d = read_csv("determinism")
    sn = np.array([r["saniye"] for r in d])
    a = np.array([r["kosu_a"] for r in d]); b = np.array([r["kosu_b"] for r in d])
    fark = np.array([r["fark"] for r in d])
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(ps.SINGLE_COL[0], 3.0),
                                   sharex=True, gridspec_kw={"height_ratios":[3,1]})
    ax1.plot(sn, a, color=ps.C_MODEL, lw=1.4, label="kosu A")
    ax1.plot(sn, b, color=ps.C_ACCENT, lw=1.0, ls="--", label="kosu B")
    ax1.set_ylabel("PCB sicaklik ($^\\circ$C)")
    ax1.legend(loc="upper right")
    ax2.plot(sn, fark, color=ps.C_OLD, lw=1.0)
    ax2.set_ylabel("fark")
    ax2.set_xlabel("acilistan itibaren gecen sure (s)")
    ax2.set_ylim(-1, 1)
    ax2.text(0.5, 0.7, f"maks |A-B| = {fark.max():.1f}", transform=ax2.transAxes,
             ha="center", fontsize=7, color=ps.C_OLD)
    print("yazildi:", ps.save(fig, "fig07_determinism"))

if __name__ == "__main__": main()
