"""Run the monitoring client and simulator as separate processes over socat."""
from pathlib import Path
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    (HERE / "data").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="gnsdo-e2e-") as tmp:
        client_port, server_port = Path(tmp) / "client", Path(tmp) / "server"
        processes = []
        with (HERE / "data/client_test_server.log").open("w") as log:
            try:
                processes.append(subprocess.Popen([
                    "socat", f"pty,raw,echo=0,link={client_port}",
                    f"pty,raw,echo=0,link={server_port}"], stderr=log))
                for _ in range(100):
                    if client_port.exists() and server_port.exists():
                        break
                    time.sleep(0.05)
                else:
                    raise TimeoutError("socat PTYs not ready")
                processes.append(subprocess.Popen([
                    sys.executable, "-m", "gnsdo_simulator.main", "--port", str(server_port),
                    "--scenario", "normal", "--log-file", ""], cwd=ROOT, stdout=log, stderr=log))
                # Wait for the server's explicit port-open log before starting the client.
                for _ in range(100):
                    if "Seri port acildi" in (HERE / "data/client_test_server.log").read_text():
                        break
                    if processes[-1].poll() is not None:
                        raise RuntimeError("Simulator exited during startup")
                    time.sleep(0.05)
                else:
                    raise TimeoutError("Simulator serial port not ready")
                # The client also has a bounded serial read timeout.
                with (HERE / "data/client_test.jsonl").open("w") as output:
                    subprocess.run([sys.executable, str(HERE / "monitor_client.py"),
                                    "--port", str(client_port), "--exercise-holdover"],
                                   stdout=output, check=True, timeout=90)
                print("PASS: separate monitoring client, 62 s holdover, alarm and recovery")
            finally:
                for process in reversed(processes):
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()


if __name__ == "__main__":
    main()
