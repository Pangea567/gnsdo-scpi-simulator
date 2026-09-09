import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt, plot_style as ps
from harness import read_csv
def main():
    ps.apply_ieee_style(); d=read_csv("health_bits")
    saat=np.array([r["saat"] for r in d]); b10=np.array([r["bit10_holdover"] for r in d]); b4=np.array([r["bit4_faz"] for r in d])
    fig,ax=plt.subplots(figsize=ps.SINGLE_COL)
    # basamak grafigi: her bit ayri seviyede
    ax.step(saat,b10+2.2,where="post",color=ps.C_MODEL,lw=1.3)
    ax.step(saat,b4,where="post",color=ps.C_REAL,lw=1.3)
    ax.text(6,3.3,"0x10  holdover > 60 sn",ha="right",fontsize=7,color=ps.C_MODEL)
    ax.text(6,1.1,"0x4   faz > 210 ns",ha="right",fontsize=7,color=ps.C_REAL)
    tc=next((r["saat"] for r in d if r["bit4_faz"]==1),None)
    if tc: ax.axvline(tc,color=ps.C_OLD,ls=":",lw=0.7); ax.text(tc,-0.4,f"0x14\n{tc:.2f} sa",ha="center",fontsize=6,color=ps.C_OLD)
    ax.set_yticks([0,1,2.2,3.2]); ax.set_yticklabels(["kapalı","açık","kapalı","açık"])
    ax.set_xlabel("holdover süresi (saat)"); ax.set_ylabel("SYNC:HEALTH? biti")
    ax.set_xlim(0,6); ax.set_ylim(-0.6,3.8)
    print("yazıldı:", ps.save(fig,"fig08_health_bits"))
if __name__=="__main__": main()
