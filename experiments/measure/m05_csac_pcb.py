"""Ölçüm 05: CSAC-PCB sıcaklık ilişkisi -- model gerçeği tutturuyor mu?"""
import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np
from harness import Measurement
sys.path.insert(0, HERE)
from datetime import datetime, timedelta
from gnsdo_simulator.device_state import DeviceState, measured_csac_temperature, CSAC_PCB_TEMP_OFFSET
sys.path.append(os.path.join(HERE,".."))
from _reference import MEAS_PAIRS

def main():
    m = Measurement("csac_pcb", "CSAC = PCB + ofset ilişkisi (doğrulama)")
    st = DeviceState(); st.noise_scale = 0.0
    for pcb in np.linspace(44, 56, 61):
        st.temperature_celsius = pcb
        m.record(pcb_c=round(pcb,3), csac_model_c=measured_csac_temperature(st))
    # gerçek dört ölçümle karşılaştır
    max_res = 0.0
    for pcb_r, csac_r in MEAS_PAIRS:
        st.temperature_celsius = pcb_r
        res = abs(measured_csac_temperature(st) - csac_r)
        max_res = max(max_res, res)
    m.check(max_res < 0.10, f"model, gerçek 4 ölçümü ±0.10°C içinde tutuyor (maks {max_res:.3f})")
    m.check(abs(CSAC_PCB_TEMP_OFFSET - 1.32) < 1e-9, "ofset gerçek ortalama +1.32°C")
    return m.finish()

if __name__ == "__main__": sys.exit(0 if main() else 1)
