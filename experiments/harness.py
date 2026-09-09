"""
experiments/harness.py

Olcum (Asama 1) altyapisi. Bir "olcum":
  1. Modeli/simulatoru bir parametre suprumunde CALISTIRIR,
  2. Sonucu satir satir BIRIKTIRIR ve CSV'ye yazar (kalici veri eseri),
  3. Beklenen degismezleri DOGRULAR (assert -> PASS/FAIL),
  4. Kosuyu log'a yazar (zaman damgasi + git commit + sonuc).

Boylece cizim asamasi (plot/) yalnizca CSV okur; simulasyonu bir daha
calistirmaz. Veri ile sunum tamamen ayrilir.
"""
import csv
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
LOG = ROOT / "log"
DATA.mkdir(exist_ok=True)
LOG.mkdir(exist_ok=True)


def _git_sha():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
            stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return "unknown"


class Measurement:
    """
    Tek bir olcum kosusu. Kullanim:

        m = Measurement("holdover", "Holdover'da TINT birikimi")
        for h in saatler:
            m.record(saat=h, tint_ns=...)
        m.check(m.rows[-1]["tint_ns"] > m.rows[0]["tint_ns"], "monoton artis")
        m.finish()   # CSV + log yazar, PASS/FAIL basar
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.rows: list[dict] = []
        self.checks: list[tuple[str, bool]] = []

    def record(self, **cols):
        self.rows.append(cols)

    def check(self, condition: bool, label: str):
        self.checks.append((label, bool(condition)))
        return condition

    @property
    def passed(self) -> bool:
        return all(ok for _, ok in self.checks)

    def save_csv(self) -> Path:
        out = DATA / f"{self.name}.csv"
        if not self.rows:
            return out
        cols = list(self.rows[0].keys())
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(self.rows)
        return out

    def finish(self) -> bool:
        csv_path = self.save_csv()
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sha = _git_sha()
        status = "PASS" if self.passed else "FAIL"
        with open(LOG / "runs.log", "a") as f:
            f.write(f"[{stamp}] {sha} {status} {self.name} "
                    f"({len(self.rows)} satir, {len(self.checks)} kontrol)\n")
            for label, ok in self.checks:
                f.write(f"    {'ok ' if ok else 'HATA'} {label}\n")
        print(f"{status}  {self.name}: {len(self.rows)} satir -> {csv_path.name}")
        for label, ok in self.checks:
            print(f"   {'ok ' if ok else 'HATA'} {label}")
        return self.passed


def read_csv(name: str) -> list[dict]:
    """Cizim asamasi icin: bir olcumun CSV'sini okur (degerler float'a cevrilir)."""
    path = DATA / f"{name}.csv"
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            conv = {}
            for k, v in r.items():
                try:
                    conv[k] = float(v)
                except (ValueError, TypeError):
                    conv[k] = v
            rows.append(conv)
    return rows
