import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt, plot_style as ps
from harness import read_csv
from _reference import EFC_PAIRS
def main():
    ps.apply_ieee_style(); d=read_csv("efc")
    rel=np.array([r["rel_pct"] for r in d]); ab=np.array([r["abs_model_ppt"] for r in d])
    rr=np.array([r for r,_ in EFC_PAIRS]); ar=np.array([a for _,a in EFC_PAIRS])
    fig,ax=plt.subplots(figsize=ps.SINGLE_COL)
    ax.plot(rel,ab,color=ps.C_MODEL,lw=1.2,label=r"model: Abs $= 200\times$Rel")
    ax.scatter(rr,ar,color=ps.C_REAL,s=32,zorder=5,edgecolor="white",linewidth=0.5,label="gerçek cihaz (4 ölçüm)")
    ax.set_xlabel("EFControl Relative (%)"); ax.set_ylabel("EFControl Absolute (ppt)")
    ax.legend(loc="upper left")
    print("yazıldı:", ps.save(fig,"fig09_efc_relation"))
if __name__=="__main__": main()
