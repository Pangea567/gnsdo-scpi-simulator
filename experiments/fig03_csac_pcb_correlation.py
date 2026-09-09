"""
fig03: CSAC-PCB sicaklik iliskisi -- sadakat dogrulamasi.

Gercek cihazin dort MEAS? ciftinde CSAC her zaman PCB'den ~+1.32 C
yuksek. Model bu iliskiyi yeniden uretiyor. Zaman damgasi gerektirmez.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
import matplotlib.pyplot as plt
import plot_style as ps
from _reference import MEAS_PAIRS
from gnsdo_simulator.device_state import CSAC_PCB_TEMP_OFFSET

def main():
    ps.apply_ieee_style()
    pcb = np.array([p for p, _ in MEAS_PAIRS])
    csac = np.array([c for _, c in MEAS_PAIRS])

    fig, ax = plt.subplots(figsize=ps.SINGLE_COL)
    x = np.linspace(pcb.min() - 1.5, pcb.max() + 1.5, 50)
    ax.plot(x, x + CSAC_PCB_TEMP_OFFSET, color=ps.C_MODEL, lw=1.2,
            label=fr"model: $\mathrm{{CSAC}} = \mathrm{{PCB}} + {CSAC_PCB_TEMP_OFFSET:.2f}$")
    ax.scatter(pcb, csac, color=ps.C_REAL, s=32, zorder=5, edgecolor="white",
               linewidth=0.5, label="gercek cihaz (4 olcum)")

    # her nokta icin gercek fark etiketi
    for p, c in MEAS_PAIRS:
        ax.annotate(f"+{c - p:.2f}", (p, c), textcoords="offset points",
                    xytext=(5, -8), fontsize=6, color=ps.C_OLD)

    ax.set_xlabel("PCB sicakligi ($^\\circ$C)")
    ax.set_ylabel("CSAC sicakligi ($^\\circ$C)")
    ax.legend(loc="upper left")
    ax.set_aspect("equal", adjustable="datalim")
    print("yazildi:", ps.save(fig, "fig03_csac_pcb_correlation"))

if __name__ == "__main__":
    main()
