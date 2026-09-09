"""
Çizim 13: Simülatör mimarisi (katmanlı) + iki aşamalı deney boru hattı.
Veri üretmez; yapisal diyagram (fig05 gibi çizim-only).
"""
import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import plot_style as ps

def box(ax, x, y, w, h, text, fc, tc="black"):
    ax.add_patch(FancyBboxPatch((x,y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
                 linewidth=0.8, edgecolor="#333333", facecolor=fc))
    ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=7.5, color=tc, zorder=5)

def arrow(ax, x1,y1,x2,y2, style="-|>", color="#333333"):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2), arrowstyle=style, mutation_scale=9,
                 linewidth=0.9, color=color))

def main():
    ps.apply_ieee_style()
    fig, ax = plt.subplots(figsize=(ps.DOUBLE_COL[0], 2.9))
    ax.set_xlim(0,10); ax.set_ylim(0,6); ax.axis("off")

    O = ps.OKABE_ITO
    # istemci
    box(ax, 0.3, 4.6, 2.2, 0.9, "istemci yazılımı\n(test uygulaması)", "#ffffff")
    # sanal seri port
    box(ax, 0.3, 3.0, 2.2, 0.9, "sanal seri port\n(socat / PTY)", O[4]+"55")
    # simulator katmanlari (kutu icinde)
    box(ax, 3.4, 0.4, 6.2, 5.2, "", "#f4f4f4")
    ax.text(6.5, 5.25, "cihaz simülatörü", ha="center", fontsize=8, style="italic", color="#555")
    box(ax, 3.7, 4.35, 5.6, 0.75, "serial_server  —  bayt ↔ satır, bilinmeyen komut: Command Error", "#ffffff")
    box(ax, 3.7, 3.4, 5.6, 0.75, "scpi_parser  —  komutu handler'a yönlendirir (kısa/uzun form)", "#ffffff")
    box(ax, 3.7, 2.45, 5.6, 0.75, "device_state  —  cihazın hafızası (tek okuma noktası)", O[2]+"55")
    box(ax, 3.7, 1.5, 5.6, 0.75, "models/  —  saf fizik: holdover · gürültü · ısınma", O[3]+"55")
    box(ax, 3.7, 0.62, 5.6, 0.62, "commands/  —  SYNC · GPS · MEAS · CSAC · SERVO · GYRO · ...", "#ffffff")

    # akis oklari
    arrow(ax, 1.4,4.6, 1.4,3.92)   # istemci -> pty
    arrow(ax, 1.4,3.92, 1.4,4.55, style="<|-")  # cift yon
    arrow(ax, 2.5,3.45, 3.7,4.7)   # pty -> serial_server
    ax.text(1.65,4.15,"SCPI\nkomut/cevap",fontsize=6,color="#555",va="center")
    # ic dikey akis
    for y1,y2 in [(4.35,4.15),(3.4,3.2),(2.45,2.25)]:
        arrow(ax, 6.5,y1, 6.5,y2)
    ax.text(9.15,2.82,"okur",fontsize=6,color="#555")

    print("yazıldı:", ps.save(fig, "fig13_architecture"))

if __name__=="__main__": main()
