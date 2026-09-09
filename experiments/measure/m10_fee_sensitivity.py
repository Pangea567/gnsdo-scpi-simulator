"""Ölçüm 10: Holdover birikim hızı FEE'ye (y0) bağlı -- gerçek 3 örnek."""
import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np
from harness import Measurement
from gnsdo_simulator.models.holdover import holdover_tint_seconds
from _reference import FEE_SAMPLES
def main():
    m = Measurement("fee_sensitivity", "FEE duyarlılığı: birikim hızı y0 ile ölçekleniyor")
    fees = sorted(FEE_SAMPLES)  # 1.31e-11, 1.59e-11, 2.49e-11
    for h in np.linspace(0,6,241):
        t=h*3600
        row={"saat":round(h,4)}
        for f in fees:
            row[f"fee_{f:.2e}"] = holdover_tint_seconds(t,0.0,f)*1e9
        m.record(**row)
    son=m.rows[-1]
    dus=son[f"fee_{fees[0]:.2e}"]; yuk=son[f"fee_{fees[-1]:.2e}"]
    m.check(yuk > dus, "yüksek FEE daha hızlı birikir")
    m.check(abs(yuk/dus - fees[-1]/fees[0]) < 0.05, "birikim ~ FEE ile orantılı")
    return m.finish()
if __name__=="__main__": sys.exit(0 if main() else 1)
