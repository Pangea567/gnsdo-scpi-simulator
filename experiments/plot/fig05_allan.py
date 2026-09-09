import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt, plot_style as ps
from _reference import ADEV_TAU, ADEV_SIGMA
def main():
    ps.apply_ieee_style()
    tau=np.array(ADEV_TAU,float); sig=np.array(ADEV_SIGMA,float)
    fig,ax=plt.subplots(figsize=ps.SINGLE_COL)
    ax.loglog(tau,sig,marker="o",ms=3.5,color=ps.C_MODEL,label="kılavuz Şek. 2.19 (GPS kilitli)")
    t0,s0=200.0,7.21e-12; tr=np.array([t0,4000.0])
    ax.loglog(tr,s0*(tr/t0)**-1.0,ls="--",lw=0.7,color=ps.C_OLD,label=r"$\tau^{-1}$")
    ax.loglog(tr,s0*(tr/t0)**-0.5,ls=":",lw=0.9,color=ps.C_ACCENT,label=r"$\tau^{-1/2}$")
    ax.set_xlabel(r"ortalama zamanı $\tau$ (s)"); ax.set_ylabel(r"Allan sapması $\sigma_y(\tau)$")
    ax.grid(True,which="both"); ax.legend(loc="lower left")
    print("yazıldı:", ps.save(fig,"fig05_allan_deviation"))
if __name__=="__main__": main()
