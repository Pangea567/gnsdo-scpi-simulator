"""Ölçüm 09: İki TINT ölçümü -- ana (Rb↔GNSS) birikiyor, filtre (OCXO↔Rb) birikmiyor."""
import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np
from datetime import datetime, timedelta
from harness import Measurement
from gnsdo_simulator.device_state import DeviceState, enter_holdover, current_tint_seconds, filter_tint_seconds
def main():
    m = Measurement("two_loop_tint", "Ana vs filtre TINT (holdover'da ayrışma)")
    st = DeviceState(); st.noise_scale=0.0
    enter_holdover(st); anchor=datetime.now()
    for h in np.linspace(0.001,6,300):
        st.holdover_started_at = anchor - timedelta(hours=float(h))
        m.record(saat=round(h,4),
                 ana_ns=current_tint_seconds(st)*1e9,
                 filtre_ns=filter_tint_seconds(st)*1e9)
    ana=[r["ana_ns"] for r in m.rows]; filt=[abs(r["filtre_ns"]) for r in m.rows]
    m.check(ana[-1] > 200, "ana TINT 6 saatte >200 ns birikiyor")
    m.check(max(filt) < 5, "filtre TINT ±5 ns içinde kalıyor (birikmiyor)")
    m.check(ana[-1] > 40*max(filt), "ana, filtreden en az 40× büyük")
    return m.finish()
if __name__=="__main__": sys.exit(0 if main() else 1)
