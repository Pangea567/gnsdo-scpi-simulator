import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np, matplotlib.pyplot as plt, plot_style as ps
from harness import read_csv
def main():
    ps.apply_ieee_style(); d=read_csv("cold_start")
    dk=np.array([r["dakika"] for r in d])
    temp=np.array([r["pcb_c"] for r in d]); volt=np.array([r["tcxo_v"] for r in d]); besl=np.array([r["besleme_v"] for r in d])
    fig,axes=plt.subplots(3,1,figsize=(ps.SINGLE_COL[0],3.8),sharex=True)
    for ax,y,c,lab in [(axes[0],temp,ps.C_MODEL,"PCB sıcaklık\n($^\\circ$C)"),
                        (axes[1],volt,ps.C_ALT,"TCXO voltaj\n(V)"),
                        (axes[2],besl,ps.C_ACCENT,"besleme voltaj\n(V)")]:
        ax.plot(dk,y,color=c,lw=1.0); ax.set_ylabel(lab); ax.margins(y=0.25)
    axes[0].set_title("soğuk başlangıç: sıcaklık ısınır, sonra gürültüyle gezinir",fontsize=7)
    axes[-1].set_xlabel("açılıştan itibaren geçen süre (dakika)")
    print("yazıldı:", ps.save(fig,"fig06_cold_start"))
if __name__=="__main__": main()
