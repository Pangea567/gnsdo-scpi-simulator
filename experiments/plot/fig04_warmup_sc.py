"""
fig04_warmup_sc.py -- fig04'un TEK SUTUN (single-column) varyanti.

ELECO bildirisinin 5 sayfalik surumu icin uretildi: cift sutunu asan
genis fig04 yerine tek sutuna sigan, ama etiketleri sikismayan bir
surum. Icerik ve veri fig04_warmup.py ile ayni kaynaktan
(measure/warmup CSV) gelir; yalnizca sekil boyutu ve etiket
yerlesimi tek sutuna gore ayarlanmistir.

Cikti: experiments/figures/fig04_warmup_ramp_sc[_tr].pdf/.png
"""

import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))

import numpy as np
import matplotlib.pyplot as plt
import plot_style as ps
from plot_style import L
from harness import read_csv
from _reference import PCB_OBSERVED_MIN, PCB_OBSERVED_MAX
from gnsdo_simulator.models.warmup import ATOMIC_LOCK_SECONDS, GNSS_LOCK_SECONDS


def main():
    ps.apply_ieee_style()
    d = read_csv("warmup")
    dk = np.array([r["dakika"] for r in d])
    temp = np.array([r["pcb_c"] for r in d])
    xmax = dk.max()
    a = ATOMIC_LOCK_SECONDS / 60
    g = min(GNSS_LOCK_SECONDS / 60, xmax)

    # Tek sutun genisligi, alcak yukseklik: dikeyde yer acar, yatayda ferah kalir.
    fig, ax = plt.subplots(figsize=(ps.SINGLE_COL[0], 1.85), constrained_layout=True)

    # Servo durum bantlari (0: isinma, 2: kilitleniyor, 6: kilitli)
    ax.axvspan(0, a, color=ps.OKABE_ITO[1], alpha=0.10)
    ax.axvspan(a, g, color=ps.OKABE_ITO[2], alpha=0.10)
    ax.axvspan(g, xmax, color=ps.OKABE_ITO[3], alpha=0.10)

    # Bant etiketleri: dar 0-2 dk bandi icin dikey, digerleri yatay ve kucuk.
    ax.text(a / 2, 25.5, L("s0", "d0"), ha="center", va="bottom",
            fontsize=6, color=ps.C_OLD, rotation=90)
    ax.text((a + g) / 2, 51.5, L("state 2 · locking", "durum 2 · kilitleniyor"),
            ha="center", va="top", fontsize=6, color=ps.C_OLD)
    ax.text((g + xmax) / 2, 51.5, L("state 6", "durum 6"),
            ha="center", va="top", fontsize=6, color=ps.C_OLD)

    # Gozlenen PCB araligi (gercek cihaz kayitlari)
    ax.axhspan(PCB_OBSERVED_MIN, PCB_OBSERVED_MAX, color=ps.C_REAL, alpha=0.10)
    ax.text(6.5, 44.5, L("recorded range", "gözlenen aralık"),
            ha="left", va="center", fontsize=6, color=ps.C_REAL)

    ax.plot(dk, temp, color=ps.C_MODEL, lw=1.6,
            label=L("PCB temp. (model)", "PCB sıcaklığı (model)"))
    ax.axhline(52.8, color=ps.C_OLD, ls=":", lw=0.8)
    ax.axvline(g, color=ps.C_ALT, ls="--", lw=1.0)
    ax.annotate(r"LOCKED?$=1$", xy=(g, 30), xytext=(g - 1.2, 27),
                ha="right", fontsize=6, color=ps.C_ALT,
                arrowprops=dict(arrowstyle="->", color=ps.C_ALT, lw=0.7))

    ax.set_xlabel(L("time since power-on (min)", "açılıştan itibaren süre (dk)"))
    ax.set_ylabel(L(r"temperature ($^\circ$C)", r"sıcaklık ($^\circ$C)"))
    ax.set_xlim(0, xmax)
    ax.set_ylim(24, 54)
    ax.legend(loc="center right", fontsize=6)

    print("written:", ps.save(fig, "fig04_warmup_ramp_sc"))


if __name__ == "__main__":
    main()
