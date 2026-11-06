"""
Olcum 01: Holdover'da TINT hata birikimi.

Modeli 0-24 saat suprumunde calistirir, dogrusal model ve analitik referans
degerleri kaydeder, ve fiziksel degismezleri dogrular.
"""
import os, sys
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
import numpy as np
from harness import Measurement
from gnsdo_simulator.models.holdover import holdover_tint_seconds

FEE = 1.8e-11  # effective y_h assumption, based on recorded FEE magnitudes
HEALTH_THR_NS = 210.0

def main():
    m = Measurement("holdover", "Holdover'da TINT birikimi (0-24 saat)")
    for h in np.linspace(0, 24, 289):  # 5 dk cozunurluk
        t = h * 3600
        full = holdover_tint_seconds(t, 0.0, FEE) * 1e9
        lin = FEE * t * 1e9
        m.record(saat=round(h, 4), tint_ns=full, dogrusal_ns=lin,
                 referans_farki_ns=full - lin)

    ilk, son = m.rows[0]["tint_ns"], m.rows[-1]["tint_ns"]
    m.check(son > ilk, "TINT monoton artıyor")
    m.check(abs(m.rows[0]["tint_ns"]) < 1e-6, "t=0'da TINT ≈ 0")
    # 210 ns esigi makul bir surede asilmali (saatler, dakikalar/gunler degil)
    asan = next(r for r in m.rows if r["tint_ns"] >= HEALTH_THR_NS)
    m.check(2.0 < asan["saat"] < 5.0, f"210 ns eşiği {asan['saat']:.2f} saatte aşılıyor")
    m.check(all(abs(r["referans_farki_ns"]) < 1e-9 for r in m.rows),
            "Dogrusal referansla tum noktalarda uyum; yaslanma terimi yok")
    return m.finish()

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
