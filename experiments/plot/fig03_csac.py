import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt, plot_style as ps
from harness import read_csv
from _reference import MEAS_PAIRS
def main():
    ps.apply_ieee_style(); d=read_csv("csac_pcb")
    x=np.array([r["pcb_c"] for r in d]); y=np.array([r["csac_model_c"] for r in d])
    pr=np.array([p for p,_ in MEAS_PAIRS]); cr=np.array([c for _,c in MEAS_PAIRS])
    fig,ax=plt.subplots(figsize=ps.SINGLE_COL)
    ax.plot(x,y,color=ps.C_MODEL,lw=1.2,label="model: CSAC = PCB + 1.32")
    ax.scatter(pr,cr,color=ps.C_REAL,s=32,zorder=5,edgecolor="white",linewidth=0.5,label="gerçek cihaz (4 ölçüm)")
    for p,c in MEAS_PAIRS:
        ax.annotate(f"+{c-p:.2f}",(p,c),textcoords="offset points",xytext=(5,-8),fontsize=6,color=ps.C_OLD)
    ax.set_xlabel("PCB sıcaklığı ($^\\circ$C)"); ax.set_ylabel("CSAC sıcaklığı ($^\\circ$C)")
    ax.legend(loc="upper left"); ax.set_aspect("equal",adjustable="datalim")
    print("yazıldı:", ps.save(fig,"fig03_csac_pcb"))
if __name__=="__main__": main()
