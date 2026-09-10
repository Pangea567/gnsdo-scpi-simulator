import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt, plot_style as ps
from plot_style import L
from harness import read_csv
from _reference import PCB_OBSERVED_MIN, PCB_OBSERVED_MAX
from gnsdo_simulator.models.warmup import ATOMIC_LOCK_SECONDS, GNSS_LOCK_SECONDS
def main():
    ps.apply_ieee_style(); d=read_csv("warmup")
    dk=np.array([r["dakika"] for r in d]); temp=np.array([r["pcb_c"] for r in d]); xmax=dk.max()
    a=ATOMIC_LOCK_SECONDS/60; g=min(GNSS_LOCK_SECONDS/60,xmax)
    fig,ax=plt.subplots(figsize=(ps.DOUBLE_COL[0],2.6), constrained_layout=True)
    ax.axvspan(0,a,color=ps.OKABE_ITO[1],alpha=0.10); ax.axvspan(a,g,color=ps.OKABE_ITO[2],alpha=0.10); ax.axvspan(g,xmax,color=ps.OKABE_ITO[3],alpha=0.10)
    labs=[(a/2,L("state 0\nwarm-up","durum 0\nısınma")),((a+g)/2,L("state 2\nlocking","durum 2\nkilitleniyor")),((g+xmax)/2,L("state 6\nlocked","durum 6\nkilitli"))]
    for x,lb in labs: ax.text(x,51.5,lb,ha="center",va="top",fontsize=7,color=ps.C_OLD)
    ax.axhspan(PCB_OBSERVED_MIN,PCB_OBSERVED_MAX,color=ps.C_REAL,alpha=0.10)
    ax.text(xmax*0.995,(PCB_OBSERVED_MIN+PCB_OBSERVED_MAX)/2,L("recorded\nrange","gözlenen\naralık"),ha="right",va="center",fontsize=7,color=ps.C_REAL)
    ax.plot(dk,temp,color=ps.C_MODEL,lw=1.6,label=L("PCB temperature (model)","PCB sıcaklığı (model)"))
    ax.axhline(52.8,color=ps.C_OLD,ls=":",lw=0.8); ax.axvline(g,color=ps.C_ALT,ls="--",lw=1.0)
    ax.annotate(r"SYNC:LOCKED? $=1$",xy=(g,30),xytext=(g-1.0,27.5),ha="right",fontsize=7,color=ps.C_ALT,arrowprops=dict(arrowstyle="->",color=ps.C_ALT,lw=0.7))
    ax.set_xlabel(L("time since power-on (minutes)","açılıştan itibaren süre (dakika)"))
    ax.set_ylabel(L(r"temperature ($^\circ$C)",r"sıcaklık ($^\circ$C)"))
    ax.set_xlim(0,xmax); ax.set_ylim(24,54); ax.legend(loc="center right")
    print("written:", ps.save(fig,"fig04_warmup_ramp"))
if __name__=="__main__": main()
