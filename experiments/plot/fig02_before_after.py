import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt, plot_style as ps
from harness import read_csv
def main():
    ps.apply_ieee_style(); d=read_csv("holdover")
    saat=np.array([r["saat"] for r in d]); yeni=np.array([r["tint_ns"] for r in d])
    saat=saat[saat<=6]; yeni=yeni[:len(saat)]; eski=np.full_like(saat,850.0)
    fig,ax=plt.subplots(figsize=ps.SINGLE_COL)
    ax.fill_between(saat,yeni,eski,color=ps.C_ACCENT,alpha=0.18,label="eski modelin gizlediği fark")
    ax.plot(saat,eski,color=ps.C_OLD,ls="--",label="eski: sabit 850 ns")
    ax.plot(saat,yeni,color=ps.C_MODEL,label="yeni: fiziksel model")
    ax.set_xlabel("holdover süresi (saat)"); ax.set_ylabel("SYNC:TINT? (ns)")
    ax.set_xlim(0,6); ax.legend(loc="center right")
    print("yazıldı:", ps.save(fig,"fig02_before_after"))
if __name__=="__main__": main()
