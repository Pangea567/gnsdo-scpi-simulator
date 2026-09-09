"""
Ölçüm 03: Soğuk başlangıçta gözlenen ölçümler (gürültü açık).

Bir istemcinin cihazı fişe taktığı andan itibaren GERÇEKTE gördüğü şey:
PCB sıcaklığı ortam sıcaklığından ısınır (warmup rampası), sonra
kararlı değerin etrafında gezinir; voltaj ve besleme voltajı sabitin
etrafında titreşir. Warmup + gürültü birlikte.
"""
import os, sys
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
import numpy as np
from datetime import datetime, timedelta
from harness import Measurement
from gnsdo_simulator.device_state import (
    DeviceState, measured_temperature, measured_voltage,
    measured_power_supply, current_servo_state, is_locked)

def main():
    m = Measurement("cold_start", "Soğuk başlangıç: warmup + gürültü (0-20 dk)")
    st = DeviceState()
    st.temperature_celsius = 52.8      # ulaşılacak kararlı değer
    st.ambient_temperature_c = 25.0    # açılış sıcaklığı
    anchor = datetime.now()
    for dk in np.linspace(0, 20, 481):  # 10 sn çözünürlük
        st.warmup_started_at = anchor - timedelta(minutes=float(dk))
        st.process_started_at = anchor - timedelta(minutes=float(dk))
        m.record(dakika=round(dk, 3),
                 pcb_c=measured_temperature(st),
                 tcxo_v=measured_voltage(st),
                 besleme_v=measured_power_supply(st),
                 servo_state=current_servo_state(st),
                 locked=int(is_locked(st)))
    temps = [r["pcb_c"] for r in m.rows]
    m.check(temps[0] < 27, "başlangıçta ortam sıcaklığına yakın (soğuk)")
    m.check(temps[-1] > 50, "90 dk sonra kararlı sıcaklığa ulaştı")
    m.check(max(temps[:6]) < max(temps[-6:]), "sıcaklık ısınma yönünde arttı")
    # determinizm: aynı anı iki kez sor
    st.warmup_started_at = anchor - timedelta(minutes=45)
    st.process_started_at = anchor - timedelta(minutes=45)
    m.check(measured_temperature(st) == measured_temperature(st),
            "aynı anda iki sorgu aynı değer (determinizm)")
    # besleme voltajı ısınmadan bağımsız (yalnız gürültü) -> dar bantta
    besl = [r["besleme_v"] for r in m.rows]
    m.check(max(besl) - min(besl) < 0.3, "besleme voltajı dar bantta gezinir")
    return m.finish()

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
