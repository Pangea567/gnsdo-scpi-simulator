"""Olcum 04: Iki BAGIMSIZ kosu birebir ayni seriyi uretir mi?"""
import os, sys
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
import numpy as np
from datetime import datetime, timedelta
from harness import Measurement
from gnsdo_simulator.device_state import DeviceState, measured_temperature

def main():
    m = Measurement("determinism", "İki bağımsız koşu — aynı çıktı")
    anchor = datetime.now()
    stA = DeviceState(); stA.temperature_celsius = 52.8
    stB = DeviceState(); stB.temperature_celsius = 52.8
    max_fark = 0.0
    for sn in np.linspace(0, 300, 301):
        stA.process_started_at = anchor - timedelta(seconds=float(sn))
        stB.process_started_at = anchor - timedelta(seconds=float(sn))
        a = measured_temperature(stA); b = measured_temperature(stB)
        max_fark = max(max_fark, abs(a - b))
        m.record(saniye=round(sn, 2), kosu_a=a, kosu_b=b, fark=abs(a - b))
    m.check(max_fark == 0.0, f"iki koşu birebir aynı (maks fark={max_fark})")
    return m.finish()

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
