import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt, plot_style as ps
from plot_style import L
from harness import read_csv
from _reference import MEAS_PAIRS
from gnsdo_simulator.device_state import CSAC_PCB_TEMP_OFFSET
def main():
    ps.apply_ieee_style(); d=read_csv("csac_pcb")
    x=np.array([r["pcb_c"] for r in d]); y=np.array([r["csac_model_c"] for r in d])
    pr=np.array([p for p,_ in MEAS_PAIRS]); cr=np.array([c for _,c in MEAS_PAIRS])
    resid=max(abs(cr-(pr+CSAC_PCB_TEMP_OFFSET)))
    fig,ax=plt.subplots(figsize=ps.SINGLE_COL, constrained_layout=True)
    ax.plot(x,y,color=ps.C_MODEL,lw=1.4,label=r"model: CSAC $=$ PCB $+\,1.32\,^\circ$C")
    ax.scatter(pr,cr,color=ps.C_REAL,s=34,zorder=5,edgecolor="white",linewidth=0.6,
               label=L("recorded device (4 samples)","gerçek cihaz (4 örnek)"))
    ax.text(0.05,0.90,L("max residual","maks. artık")+f" {resid:.2f}$\\,^\\circ$C",
            transform=ax.transAxes,fontsize=7,color=ps.C_OLD)
    ax.set_xlabel(L(r"PCB temperature ($^\circ$C)",r"PCB sıcaklığı ($^\circ$C)"))
    ax.set_ylabel(L(r"CSAC temperature ($^\circ$C)",r"CSAC sıcaklığı ($^\circ$C)"))
    ax.legend(loc="lower right"); ax.set_aspect("equal",adjustable="datalim")
    print("written:", ps.save(fig,"fig03_csac_pcb"))
if __name__=="__main__": main()
