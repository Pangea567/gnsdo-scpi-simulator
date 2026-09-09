"""Ölçüm 07: Holdover boyunca SYNC:HEALTH? bit evrimi."""
import os, sys
HERE=os.path.dirname(__file__); sys.path.insert(0, os.path.join(HERE,".."))
sys.path.insert(0, os.path.join(HERE,"..","..","src"))
import numpy as np
from datetime import datetime, timedelta
from harness import Measurement
from gnsdo_simulator.device_state import DeviceState, enter_holdover
from gnsdo_simulator.scpi_parser import SCPIParser
from gnsdo_simulator.commands.sync import register_sync_commands

def main():
    m = Measurement("health_bits", "Holdover'da SYNC:HEALTH? bit evrimi (0-6 saat)")
    st = DeviceState()
    st.process_started_at = datetime.now() - timedelta(seconds=5000)  # 0x8 karışmasın
    p = SCPIParser(); register_sync_commands(p, st)
    enter_holdover(st)
    anchor = datetime.now()
    for h in np.linspace(0.001, 6, 400):
        st.holdover_started_at = anchor - timedelta(hours=float(h))
        hexv = p.dispatch("SYNC:HEALTH?")
        val = int(hexv, 16)
        m.record(saat=round(h,4), health=val,
                 bit10_holdover=int(bool(val & 0x10)),
                 bit4_faz=int(bool(val & 0x4)))
    m.check(m.rows[0]["bit10_holdover"] == 0 or m.rows[5]["bit10_holdover"] == 1,
            "0x10 (holdover>60sn) erken yanıyor")
    m.check(any(r["bit4_faz"] == 1 for r in m.rows), "0x4 (faz>210ns) bir noktada yanıyor")
    son = m.rows[-1]
    m.check(son["health"] == 0x14, f"6 saatte HEALTH=0x14 (kılavuz örneği); gözlenen 0x{son['health']:X}")
    return m.finish()

if __name__ == "__main__": sys.exit(0 if main() else 1)
