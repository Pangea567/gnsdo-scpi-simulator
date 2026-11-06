"""Generate paper plots from the shipped models and audit recorded HELP queries.

Run from any directory with the project's Python environment.
"""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gnsdo_simulator import main
from gnsdo_simulator.device_state import DeviceState
from gnsdo_simulator.models.holdover import holdover_tint_seconds
from gnsdo_simulator.models.warmup import thermal_ramp
from gnsdo_simulator.scpi_parser import SCPIParser

# Expanded query paths from docs/gercek-cihaz-ciktilari.md, HELP block.
# HELP? itself is excluded: 66 device queries, not the command-list request.
# Use registered spellings for supported operations; this is operation
# coverage, not a test of every legal SCPI abbreviation combination.
QUERIES = """*IDN? SERV? SERV:STATE? SYNC? SYNC:SOUR:STATE?
SYNC:HOLD:DUR? SYNC:HOLD:STATE? SYNC:TINT? SYNC:TINT:CSAC?
SYNC:TINT:FILTER? SYNC:FEE? SYNC:LOCKED? SYNC:HEALTH? MAC?
MAC:RS232? MAC:STEER? MAC:STATUS? MAC:MODE? MAC:DDSCENTER?
MAC:TECCONTROL? MAC:TCXO? MAC:SIGNAL? MAC:HEATPACKAGE?
MAC:TEMPERATURE? MAC:SN? MAC:FWREV? MAC:LIFETIME?
DIAG? DIAG:ROSC:EFC:REL? DIAG:ROSC:EFC:REL:CSAC?
DIAG:ROSC:EFC:REL:FILTER? DIAG:ROSC:EFC:ABS?
DIAG:ROSC:EFC:ABS:CSAC? DIAG:ROSC:EFC:ABS:FILTER? DIAG:LIFE:COUN?
GPS? GPS:REF:PULSE:SAWTOOTH? GPS:SURV:STAT? GPS:DYNAMIC:STATE?
GPS:SAT:TRAC:COUN? GPS:SAT:VIS:COUN? GPS:POS? GPS:POS:ECEF?
GPS:JAM? GPS:FWVER? GYRO? GYRO:GLOAD? MEAS? MEAS:TEMP?
MEAS:VOLT? MEAS:CURR? MEAS:POW? PTIME? PTIME:DATE? PTIME:TIME?
PTIME:TIME:STR? PTIME:TINT? PTIME:LEAP? PTIME:LEAP:PEND?
PTIME:LEAP:ACC? PTIME:LEAP:DATE? PTIME:LEAP:DUR?
SYST:STAT? SYST:ID? SYST:ID:SN? SYST:ID:HWREV?""".split()


def write_csv(name, header, rows):
    with (HERE / "data" / name).open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def generate():
    (HERE / "data").mkdir(exist_ok=True)
    write_csv("holdover.csv", ["hours", "tint_ns"], (
        (t / 3600, holdover_tint_seconds(t, 0.0, 1.8e-11) * 1e9)
        for t in range(0, 86401, 300)))
    write_csv("warmup.csv", ["minutes", "pcb_c"], (
        (t / 60, thermal_ramp(t, 52.8, 25.0, 90.0))
        for t in range(0, 1501, 10)))
    assert abs(holdover_tint_seconds(3600, 0, 1.8e-11) - 64.8e-9) < 1e-18
    assert abs(holdover_tint_seconds(86400, 0, 1.8e-11) - 1.5552e-6) < 1e-18
    state, parser = DeviceState(), SCPIParser()
    for name, register in vars(main).items():
        if name.startswith("register_") and name.endswith("_commands"):
            register(parser, state)
    rows = [(q, "supported" if parser.dispatch(q) is not None else "unsupported")
            for q in QUERIES]
    assert len(set(QUERIES)) == 66
    assert sum(status == "supported" for _, status in rows) == 50
    write_csv("query_coverage.csv", ["query", "status"], rows)
    paths = sorted((ROOT / "src/gnsdo_simulator").rglob("*.py"))
    paths += sorted((ROOT / "configs").glob("*.yaml"))
    paths += [Path(__file__).resolve(), HERE / "monitor_client.py", HERE / "run_client_test.py",
              ROOT / "docs/gercek-cihaz-ciktilari.md"]
    metadata = {
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in paths},
        "holdover": {"x0_seconds": 0, "y_h": 1.8e-11,
                     "threshold_seconds": 210e-9, "crossing_hours": 210e-9 / 1.8e-11 / 3600},
        "warmup": {"start_c": 25, "final_c": 52.8, "tau_seconds": 90},
        "provenance": "Model outputs, not physical-device time-series measurements",
        "coverage": {"queries_excluding_HELP": 66, "supported": 50, "unsupported": 16},
    }
    (HERE / "data/manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("PASS: model plot data and 50/66 query coverage generated")


if __name__ == "__main__":
    generate()
