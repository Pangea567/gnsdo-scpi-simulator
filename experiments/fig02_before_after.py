"""
fig02: Once/sonra -- statik (eski) vs dinamik (yeni) TINT.

Bildirinin "ne degistirdik" gorseli. Eski kod holdover'da SABIT 850 ns
donuyordu; yeni model birikimi + jitter'i gosteriyor. Ayni eksende.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
from style import apply_style, save, COLORS, COL_WIDTH
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from gnsdo_simulator.device_state import DeviceState, enter_holdover, current_tint_seconds

def main():
    apply_style()
    st = DeviceState()
    enter_holdover(st)
    t0 = st.holdover_started_at

    hours = np.linspace(0, 6, 400)
    yeni = []
    for h in hours:
        # holdover baslangicini geriye tarihleyerek "h saat gecti" kur
        st.holdover_started_at = datetime.now() - timedelta(hours=float(h))
        yeni.append(current_tint_seconds(st) * 1e9)
    yeni = np.array(yeni)
    eski = np.full_like(hours, 850.0)  # eski sabit deger

    fig, ax = plt.subplots(figsize=(COL_WIDTH, 2.5))
    ax.plot(hours, eski, color=COLORS["old"], ls="--",
            label="eski: sabit 850 ns")
    ax.plot(hours, yeni, color=COLORS["model"],
            label="yeni: fiziksel model")
    ax.set_xlabel("holdover suresi (saat)")
    ax.set_ylabel("SYNC:TINT? (ns)")
    ax.set_xlim(0, 6)
    ax.legend(loc="center right")
    out = save(fig, "fig02_before_after")
    print("yazildi:", out)

if __name__ == "__main__":
    main()
