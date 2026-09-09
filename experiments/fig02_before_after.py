"""
fig02: Once/sonra -- eski statik model gercek hatayi GIZLIYORDU.

Eski kod holdover'da sabit 850 ns donuyordu. Golgeli alan, eski modelin
gormedigi (ve dolayisiyla istemciye yanlis bildirdigi) hatayi gosterir.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plot_style as ps
from gnsdo_simulator.device_state import DeviceState, enter_holdover, current_tint_seconds

def main():
    ps.apply_ieee_style()
    st = DeviceState()
    st.noise_scale = 0.0  # trend acikca gorunsun; jitter ayri sekilde
    enter_holdover(st)
    hours = np.linspace(0, 6, 400)
    yeni = []
    for h in hours:
        st.holdover_started_at = datetime.now() - timedelta(hours=float(h))
        yeni.append(current_tint_seconds(st) * 1e9)
    yeni = np.array(yeni)
    eski = np.full_like(hours, 850.0)

    fig, ax = plt.subplots(figsize=ps.SINGLE_COL)
    ax.fill_between(hours, eski, yeni, where=(yeni > eski),
                    color=ps.C_ACCENT, alpha=0.18)
    ax.fill_between(hours, yeni, eski, where=(yeni <= eski),
                    color=ps.C_ACCENT, alpha=0.18,
                    label="eski modelin gizledigi fark")
    ax.plot(hours, eski, color=ps.C_OLD, ls="--", label="eski: sabit 850 ns")
    ax.plot(hours, yeni, color=ps.C_MODEL, label="yeni: fiziksel model")
    ax.set_xlabel("holdover suresi (saat)")
    ax.set_ylabel("SYNC:TINT? (ns)")
    ax.set_xlim(0, 6)
    ax.legend(loc="center right")
    print("yazildi:", ps.save(fig, "fig02_before_after"))

if __name__ == "__main__":
    main()
