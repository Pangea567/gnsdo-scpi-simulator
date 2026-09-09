import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt, plot_style as ps
from harness import read_csv
def main():
    ps.apply_ieee_style(); d=read_csv("two_loop_tint")
    saat=np.array([r["saat"] for r in d]); ana=np.array([r["ana_ns"] for r in d]); filt=np.array([r["filtre_ns"] for r in d])
    fig,ax=plt.subplots(figsize=ps.SINGLE_COL)
    ax.plot(saat,ana,color=ps.C_MODEL,label=r"ana: SYNC:TINT:CSAC? (Rb$\leftrightarrow$GNSS)")
    ax.plot(saat,filt,color=ps.C_ALT,lw=1.1,label=r"filtre: SYNC:TINT:FILTER? (OCXO$\leftrightarrow$Rb)")
    ax.axhline(0,color=ps.C_OLD,lw=0.5)
    ax.set_xlabel("holdover süresi (saat)"); ax.set_ylabel("TINT (ns)"); ax.set_xlim(0,6)
    ax.legend(loc="upper left")
    ax.text(3,30,"GNSS kaybı ana döngüyü açar,\nfiltre döngüsü Rb'ye kilitli kalır",fontsize=6.5,color=ps.C_OLD)
    print("yazıldı:", ps.save(fig,"fig11_two_loop_tint"))
if __name__=="__main__": main()
