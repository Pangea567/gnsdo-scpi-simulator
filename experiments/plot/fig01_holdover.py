import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt, plot_style as ps
from plot_style import L
from harness import read_csv
from _reference import HEALTH_PHASE_THRESHOLD_NS
def main():
    ps.apply_ieee_style(); d=read_csv("holdover")
    saat=np.array([r["saat"] for r in d]); full=np.array([r["tint_ns"] for r in d])
    m=saat<=12; saat,full=saat[m],full[m]
    fig,ax=plt.subplots(figsize=ps.SINGLE_COL, constrained_layout=True)
    ax.plot(saat,full,color=ps.C_MODEL,lw=1.6)
    thr=HEALTH_PHASE_THRESHOLD_NS
    ax.axhline(thr,color=ps.C_REAL,lw=1.0,ls="--")
    ax.text(11.8,thr+14,L("0x4 threshold (210 ns)","0x4 eşiği (210 ns)"),
            color=ps.C_REAL,fontsize=7,ha="right",va="bottom")
    tc=float(np.interp(thr,full,saat))
    ax.plot([tc],[thr],marker="o",ms=4,color=ps.C_REAL,zorder=5)
    ax.annotate(f"{tc:.1f} "+L("h","sa"),xy=(tc,thr),xytext=(tc+0.5,thr-55),
                fontsize=7,color=ps.C_REAL,arrowprops=dict(arrowstyle="-",color=ps.C_REAL,lw=0.6))
    ax.set_xlabel(L("holdover duration (hours)","holdover süresi (saat)"))
    ax.set_ylabel("TINT (ns)")
    ax.set_xlim(0,12); ax.set_ylim(0,full.max()*1.03); ax.margins(x=0)
    print("written:", ps.save(fig,"fig01_holdover_accumulation"))
if __name__=="__main__": main()
