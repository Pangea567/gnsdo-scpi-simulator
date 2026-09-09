"""Ölçüm 08: Kilitliyken TINT -- işaretli jitter, trend YOK."""
import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np
from datetime import datetime, timedelta
from harness import Measurement
from gnsdo_simulator.device_state import DeviceState, current_tint_seconds

def main():
    m = Measurement("locked_tint", "Kilitli TINT jitter (işaretli, trendsiz)")
    st = DeviceState()  # holdover yok -> kilitli
    anchor = datetime.now()
    for sn in np.linspace(0, 300, 601):  # 5 dk, 0.5 sn çözünürlük
        st.process_started_at = anchor - timedelta(seconds=float(sn))
        m.record(saniye=round(sn,3), tint_ns=current_tint_seconds(st)*1e9)
    vals = np.array([r["tint_ns"] for r in m.rows])
    m.check(abs(vals.mean()) < 3.0, f"ortalama ≈ 0 (gözlenen {vals.mean():.2f} ns)")
    m.check(vals.min() < 0 < vals.max(), "hem artı hem eksi değer (sıfır etrafında)")
    m.check(np.abs(vals).max() < 15.0, "bant ±15 ns içinde (birikme yok)")
    # trend yok: doğrusal uydurma eğimi ~0
    egim = np.polyfit(vals.size and np.arange(vals.size), vals, 1)[0]
    m.check(abs(egim) < 1e-3, f"doğrusal trend yok (eğim {egim:.2e} ns/örnek)")
    return m.finish()

if __name__ == "__main__": sys.exit(0 if main() else 1)
