import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt, plot_style as ps
from harness import read_csv
from _reference import HEALTH_PHASE_THRESHOLD_NS, FEE_SAMPLES
def main():
    ps.apply_ieee_style(); d=read_csv("fee_sensitivity")
    saat=np.array([r["saat"] for r in d])
    fees=sorted(FEE_SAMPLES)
    cols=[ps.C_ALT, ps.C_MODEL, ps.C_ACCENT]
    fig,ax=plt.subplots(figsize=ps.SINGLE_COL)
    for f,c in zip(fees,cols):
        y=np.array([r[f"fee_{f:.2e}"] for r in d])
        ax.plot(saat,y,color=c,label=fr"FEE $={f:.2e}$")
    ax.axhline(HEALTH_PHASE_THRESHOLD_NS,color=ps.C_REAL,lw=0.9,ls=":")
    ax.text(0.15,HEALTH_PHASE_THRESHOLD_NS+6,"210 ns eşiği",fontsize=7,color=ps.C_REAL)
    ax.set_xlabel("holdover süresi (saat)"); ax.set_ylabel("TINT (ns)"); ax.set_xlim(0,6)
    ax.legend(loc="upper left",title="gerçek cihaz örnekleri")
    print("yazıldı:", ps.save(fig,"fig12_fee_sensitivity"))
if __name__=="__main__": main()
