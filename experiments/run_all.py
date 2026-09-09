#!/usr/bin/env python3
"""
run_all.py -- once TUM olcumleri (measure/) kosar, sonra TUM cizimleri
(plot/) uretir. Tekrarlanabilirligin somut hali: tek komutla veri +
sekiller sifirdan uretilir.

    python3 run_all.py
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).parent

def run_group(folder):
    scripts = sorted((ROOT / folder).glob("*.py"))
    ok = True
    for s in scripts:
        print(f"\n>>> {folder}/{s.name}")
        r = subprocess.run([sys.executable, str(s)], cwd=ROOT)
        ok = ok and (r.returncode == 0)
    return ok

if __name__ == "__main__":
    print("=== AŞAMA 1: ÖLÇÜMLER (measure/) ===")
    m_ok = run_group("measure")
    print("\n=== AŞAMA 2: ÇİZİMLER (plot/) ===")
    run_group("plot")
    print("\n=== SONUÇ ===")
    print("Tüm ölçümler PASS." if m_ok else "DİKKAT: bazı ölçümler FAIL (log/runs.log).")
    sys.exit(0 if m_ok else 1)
