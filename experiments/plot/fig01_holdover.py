import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt, plot_style as ps
from harness import read_csv
from _reference import HEALTH_PHASE_THRESHOLD_NS
def main():
    ps.apply_ieee_style(); d = read_csv("holdover")
    saat=np.array([r["saat"] for r in d]); full=np.array([r["tint_ns"] for r in d]); lin=np.array([r["dogrusal_ns"] for r in d])
    fig,ax=plt.subplots(figsize=ps.SINGLE_COL)
    ax.fill_between(saat,lin,full,color=ps.C_ACCENT,alpha=0.25,label="kuadratik (yaşlanma) katkısı")
    ax.plot(saat,full,color=ps.C_MODEL,label=r"tam model $x(t)$")
    ax.plot(saat,lin,color=ps.C_OLD,ls="--",lw=1.0,label=r"yaln. doğrusal $y_0\,t$")
    ax.axhline(HEALTH_PHASE_THRESHOLD_NS,color=ps.C_REAL,lw=0.9,ls=":")
    tc=next(r["saat"] for r in d if r["tint_ns"]>=HEALTH_PHASE_THRESHOLD_NS)
    ax.annotate("HEALTH 0x4\n(210 ns)",xy=(tc,HEALTH_PHASE_THRESHOLD_NS),xytext=(tc+1.5,HEALTH_PHASE_THRESHOLD_NS+180),
                color=ps.C_REAL,fontsize=7,arrowprops=dict(arrowstyle="->",color=ps.C_REAL,lw=0.7))
    ax.set_xlabel("holdover süresi (saat)"); ax.set_ylabel("TINT (ns)")
    ax.set_xlim(0,24); ax.set_ylim(0,full.max()*1.05); ax.legend(loc="upper left")
    print("yazıldı:", ps.save(fig,"fig01_holdover_accumulation"))
if __name__=="__main__": main()
