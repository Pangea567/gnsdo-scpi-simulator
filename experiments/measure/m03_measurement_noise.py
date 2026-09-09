"""Olcum 03: Olcum gurultusu -- determinizm ve farkli zaman olcekleri."""
import os, sys
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
import numpy as np
from datetime import datetime, timedelta
from harness import Measurement
from gnsdo_simulator.device_state import (
    DeviceState, measured_temperature, measured_voltage, measured_power_supply)

def main():
    m = Measurement("measurement_noise", "Olcum gurultusu -- zamanla gezinme")
    st = DeviceState(); st.temperature_celsius = 52.8
    for sn in np.linspace(0, 600, 601):
        st.process_started_at = datetime.now() - timedelta(seconds=float(sn))
        m.record(saniye=round(sn, 2),
                 temp_c=measured_temperature(st),
                 volt=measured_voltage(st),
                 volt_psu=measured_power_supply(st))
    # determinizm: ayni anda iki kez sor -> ayni deger
    st.process_started_at = datetime.now() - timedelta(seconds=137)
    a = measured_temperature(st); b = measured_temperature(st)
    m.check(a == b, "ayni anda iki sorgu ayni deger (determinizm)")
    # gezinme: hepsi sabit degil
    m.check(len({r["temp_c"] for r in m.rows}) > 20, "sicaklik zamanla geziniyor")
    # zaman olcekleri: voltaj sicakliktan daha hizli titresir
    temp_var = sum(abs(m.rows[i+1]["temp_c"]-m.rows[i]["temp_c"]) for i in range(len(m.rows)-1))
    volt_var = sum(abs(m.rows[i+1]["volt"]-m.rows[i]["volt"]) for i in range(len(m.rows)-1))
    m.check(volt_var > temp_var, "voltaj sicakliktan hizli titresir")
    return m.finish()

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
