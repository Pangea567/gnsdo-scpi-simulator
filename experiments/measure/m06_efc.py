"""Ölçüm 06: EFControl Absolute = Relative × 200 bağıntısı (doğrulama)."""
import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np
from harness import Measurement
from gnsdo_simulator.device_state import DeviceState, measured_ef_control_absolute, EFC_ABSOLUTE_PER_PERCENT
from _reference import EFC_PAIRS

def main():
    m = Measurement("efc", "EFC Absolute = Relative × 200 (doğrulama)")
    st = DeviceState(); st.noise_scale = 0.0
    for rel in np.linspace(-1.0, 1.0, 81):
        st.diag_ef_control_relative_percent = rel
        m.record(rel_pct=round(rel,4), abs_model_ppt=measured_ef_control_absolute(st))
    m.check(abs(EFC_ABSOLUTE_PER_PERCENT - 200.0) < 1e-9, "çarpan 200")
    # gerçek dört çift bağıntıyı sağlıyor mu
    ok = all(abs(a - r*200) < 1e-6 for r, a in EFC_PAIRS)
    m.check(ok, "gerçek 4 çiftin tamamı Abs = Rel×200 sağlıyor")
    return m.finish()

if __name__ == "__main__": sys.exit(0 if main() else 1)
