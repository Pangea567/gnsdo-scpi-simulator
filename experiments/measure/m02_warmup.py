"""Olcum 02: Soguk baslangic -- sicaklik rampasi + servo durum gecisleri."""
import os, sys
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
import numpy as np
from datetime import datetime, timedelta
from harness import Measurement
from gnsdo_simulator.device_state import (
    DeviceState, current_pcb_temperature_base, current_servo_state, is_locked)
from gnsdo_simulator.models.warmup import ATOMIC_LOCK_SECONDS, GNSS_LOCK_SECONDS

def main():
    m = Measurement("warmup", "Isınma rampası + servo durum (0-60 dk)")
    st = DeviceState(); st.noise_scale = 0.0
    st.temperature_celsius = 52.8; st.ambient_temperature_c = 25.0
    for dk in np.linspace(0, 60, 361):
        st.warmup_started_at = datetime.now() - timedelta(minutes=float(dk))
        m.record(dakika=round(dk, 3),
                 pcb_c=current_pcb_temperature_base(st),
                 servo_state=current_servo_state(st),
                 locked=int(is_locked(st)))
    temps = [r["pcb_c"] for r in m.rows]
    m.check(temps == sorted(temps), "sıcaklık monoton artıyor")
    m.check(temps[0] < 26, "t=0'da ortam sıcaklığına yakın")
    m.check(temps[-1] < 52.8, "kararlı değeri aşmıyor (üstel yaklaşım)")
    # ilk 5 dk'daki artis, son 5 dk'dakinden buyuk (ustel imza)
    m.check((temps[30]-temps[0]) > (temps[-1]-temps[-31]), "üstel imza: erken artış > geç artış")
    m.check(m.rows[0]["servo_state"] == 0, "açılış durum 0 (ısınma)")
    m.check(any(r["servo_state"] == 2 for r in m.rows), "durum 2 (kilitleniyor) görülür")
    m.check(m.rows[-1]["servo_state"] == 6, "60 dk'da durum 6 (kilitli)")
    m.check(all(r["locked"] == (r["servo_state"] == 6) for r in m.rows),
            "LOCKED? yalnız durum 6'da 1")
    return m.finish()

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
