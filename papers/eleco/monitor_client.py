"""Small standalone serial monitoring client; imports no simulator modules.

The optional exercise sends holdover/recovery commands to the connected device.
"""
import argparse
import json
import time
import serial


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", required=True)
    cli.add_argument("--exercise-holdover", action="store_true")
    cli.add_argument("--hold-seconds", type=float, default=62)
    args = cli.parse_args()
    started = time.monotonic()
    with serial.Serial(args.port, 115200, timeout=3) as port:
        def query(command):
            port.write((command + "\r\n").encode("ascii"))
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                reply = port.readline().decode("ascii").strip()
                if reply:
                    return reply
            raise TimeoutError(command)

        def snapshot(stage):
            record = {"stage": stage, "elapsed_seconds": round(time.monotonic() - started, 3),
                      "identity": query("*IDN?"), "locked": int(query("SYNC:LOCKED?")),
                      "holdover": int(query("SYNC:HOLD:STATE?")),
                      "tint_seconds": float(query("SYNC:TINT?")),
                      "health": int(query("SYNC:HEALTH?"), 16)}
            record["holdover_alarm"] = record["holdover"] == 1
            record["duration_alarm"] = bool(record["health"] & 0x10)
            print(json.dumps(record), flush=True)
            return record

        first = snapshot("initial")
        if args.exercise_holdover:
            assert first["locked"] == 1 and not first["holdover_alarm"]
            port.write(b"SYNC:HOLD:INIT\r\n")
            held = snapshot("holdover_entered")
            assert held["locked"] == 0 and held["holdover_alarm"]
            time.sleep(args.hold_seconds)
            later = snapshot("holdover_waited")
            assert later["holdover_alarm"] and later["duration_alarm"]
            port.write(b"SYNC:HOLD:REC:INIT\r\n")
            restored = snapshot("recovered")
            assert restored["locked"] == 1 and not restored["holdover_alarm"]
            assert not restored["duration_alarm"]


if __name__ == "__main__":
    main()
