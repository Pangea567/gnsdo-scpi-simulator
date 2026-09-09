import os, sys
HERE=os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt
import plot_style as ps
from harness import read_csv

def main():
    ps.apply_ieee_style()
    d = read_csv("measurement_noise")
    sn = np.array([r["saniye"] for r in d])
    temp = np.array([r["temp_c"] for r in d])
    volt = np.array([r["volt"] for r in d])
    psu  = np.array([r["volt_psu"] for r in d])

    fig, axes = plt.subplots(3, 1, figsize=(ps.SINGLE_COL[0], 3.6), sharex=True)
    for ax, y, c, lab, unit in [
        (axes[0], temp, ps.C_MODEL, "PCB sicaklik", r"$^\circ$C"),
        (axes[1], volt, ps.C_ALT,  "TCXO voltaj", "V"),
        (axes[2], psu,  ps.C_ACCENT, "besleme voltaj", "V")]:
        ax.plot(sn, y, color=c, lw=1.0)
        ax.set_ylabel(f"{lab}\n({unit})")
        ax.margins(y=0.25)
    axes[-1].set_xlabel("acilistan itibaren gecen sure (s)")
    axes[0].set_title("her kanal kendi zaman olceginde geziniyor (deterministik)",
                      fontsize=7)
    print("yazildi:", ps.save(fig, "fig06_measurement_noise"))

if __name__ == "__main__": main()
