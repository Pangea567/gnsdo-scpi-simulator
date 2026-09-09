"""
fig05: Allan sapmasi -- emule edilen cihazin KARARLILIK IMZASI.

Veri: uretici kilavuzu Sekil 2.19 (Premium, GPS'e kilitli). Bu, bizim
modelimizin ciktisi DEGIL; EMULE ETTIGIMIZ CIHAZIN hedef kararliligidir.
Log-log eksende, karakteristik "tumsek": kisa vadede osilator gurultusu
baskin, uzun vadede GNSS disiplini stabiliteyi asagi ceker.

Ince kesikli referans egimleri (tau^-1 ve tau^-1/2) tumsegin sag
kolunda cizilir; verinin uzun-vade dususu tau^-1/2'ye (beyaz frekans
gurultusunun ortalanmasi) cok yakin gider.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
import matplotlib.pyplot as plt
import plot_style as ps
from _reference import ADEV_TAU, ADEV_SIGMA

def main():
    ps.apply_ieee_style()
    tau = np.array(ADEV_TAU, dtype=float)
    sig = np.array(ADEV_SIGMA, dtype=float)

    fig, ax = plt.subplots(figsize=ps.SINGLE_COL)
    ax.loglog(tau, sig, marker="o", ms=3.5, color=ps.C_MODEL,
              label="kilavuz Sek. 2.19 (GPS kilitli)")

    # referans egimleri: tumsegin tepesinden (tau0=200, s0=7.21e-12) saga
    tau0, s0 = 200.0, 7.21e-12
    tr = np.array([tau0, 4000.0])
    ax.loglog(tr, s0 * (tr / tau0) ** -1.0, ls="--", lw=0.7,
              color=ps.C_OLD, label=r"$\tau^{-1}$")
    ax.loglog(tr, s0 * (tr / tau0) ** -0.5, ls=":", lw=0.9,
              color=ps.C_ACCENT, label=r"$\tau^{-1/2}$")

    ax.set_xlabel(r"ortalama zamani $\tau$ (s)")
    ax.set_ylabel(r"Allan sapmasi $\sigma_y(\tau)$")
    ax.grid(True, which="both")
    ax.legend(loc="lower left")
    print("yazildi:", ps.save(fig, "fig05_allan_deviation"))

if __name__ == "__main__":
    main()
