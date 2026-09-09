"""
fig03: CSAC-PCB sicaklik iliskisi -- SADAKAT DOGRULAMASI.

Bu, en saglam dogrulama sekillerinden biri: gercek cihazin dort MEAS?
ciftinde CSAC sicakligi HER ZAMAN PCB'den ~+1.32 C yuksek. Modelimiz
bu iliskiyi (bagimsiz degil, turetilmis) yeniden uretiyor.

ZAMAN DAMGASI GEREKTIRMEZ -- bu yuzden rastgele-anlarda-alinmis veriyle
bile gecerli bir dogrulamadir.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
from style import apply_style, save, COLORS, COL_WIDTH
from _reference import MEAS_PAIRS
import matplotlib.pyplot as plt
from gnsdo_simulator.device_state import CSAC_PCB_TEMP_OFFSET

def main():
    apply_style()
    pcb = np.array([p for p, _ in MEAS_PAIRS])
    csac = np.array([c for _, c in MEAS_PAIRS])

    fig, ax = plt.subplots(figsize=(COL_WIDTH, 2.6))
    # model iliskisi: csac = pcb + offset
    x = np.linspace(pcb.min() - 1, pcb.max() + 1, 50)
    ax.plot(x, x + CSAC_PCB_TEMP_OFFSET, color=COLORS["model"], lw=1.1,
            label=fr"model: CSAC = PCB + {CSAC_PCB_TEMP_OFFSET:.2f}")
    ax.scatter(pcb, csac, color=COLORS["real"], s=28, zorder=5,
               label="gercek cihaz (4 olcum)")

    ax.set_xlabel("PCB sicakligi (C)")
    ax.set_ylabel("CSAC sicakligi (C)")
    ax.legend(loc="upper left")
    ax.set_aspect("equal", adjustable="datalim")
    out = save(fig, "fig03_csac_pcb_correlation")
    print("yazildi:", out)

if __name__ == "__main__":
    main()
