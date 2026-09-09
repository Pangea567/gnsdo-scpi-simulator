import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt, plot_style as ps
from harness import read_csv
def main():
    ps.apply_ieee_style(); d=read_csv("locked_tint")
    sn=np.array([r["saniye"] for r in d]); t=np.array([r["tint_ns"] for r in d])
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(ps.DOUBLE_COL[0],2.3),gridspec_kw={"width_ratios":[3,1]})
    ax1.axhline(0,color=ps.C_OLD,lw=0.6)
    ax1.plot(sn,t,color=ps.C_MODEL,lw=0.8)
    ax1.set_xlabel("süre (s)"); ax1.set_ylabel("kilitli TINT (ns)"); ax1.set_xlim(0,300)
    ax2.hist(t,bins=25,orientation="horizontal",color=ps.C_MODEL,alpha=0.8)
    ax2.axhline(t.mean(),color=ps.C_REAL,lw=1.0,ls="--")
    ax2.set_xlabel("sayım"); ax2.text(0.95,0.95,f"ort={t.mean():.2f} ns",transform=ax2.transAxes,ha="right",va="top",fontsize=6,color=ps.C_REAL)
    ax2.set_yticklabels([])
    fig.suptitle("kilitliyken TINT sıfır etrafında jitter yapar (trend yok)",fontsize=7,y=1.02)
    print("yazıldı:", ps.save(fig,"fig10_locked_tint"))
if __name__=="__main__": main()
