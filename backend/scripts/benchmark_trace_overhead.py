"""Compare disabled tracing with the completed Phase 2 engine; no DB/network required.

Run: PYTHONPATH=backend backend/.venv/bin/python backend/scripts/benchmark_trace_overhead.py
This diagnostic reports timings, not a flaky timing assertion in the test suite.
"""

import importlib.util
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

from app.services.simulators.engine import run_statevector


def main():
    source = subprocess.check_output(
        [
            "git",
            "show",
            "feature/simulator-v2-phase2:backend/app/services/simulators/engine.py",
        ],
        text=True,
    )
    with tempfile.TemporaryDirectory(prefix="iqlrs-trace-benchmark-") as directory:
        path = Path(directory) / "phase2.py"
        path.write_text(source)
        spec = importlib.util.spec_from_file_location(
            "app.services.simulators.phase2_baseline", path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cases = {
            "unitary": [{"type": "H", "qubit": q} for q in range(4)]
            + [{"type": "RY", "qubit": q, "params": {"theta": 0.71}} for q in range(4)],
            "feedforward": [
                {"type": "H", "qubit": 0},
                {
                    "type": "MEASURE",
                    "qubit": 0,
                    "destinations": [{"register": "c", "bit": 0}],
                },
                {
                    "type": "X",
                    "qubit": 1,
                    "condition": {
                        "register": "c",
                        "bit": 0,
                        "operator": "eq",
                        "value": 1,
                    },
                },
                {"type": "RESET", "qubit": 0},
            ],
        }
        for name, gates in cases.items():
            request = {"gates": gates, "num_qubits": 4, "shots": 2048, "seed": 42}
            baseline = module.run_statevector(request)
            assert run_statevector(request) == baseline
            times = {"phase2": [], "disabled": [], "one_traced_shot": []}
            runs = [
                ("phase2", module.run_statevector, request),
                ("disabled", run_statevector, request),
                (
                    "one_traced_shot",
                    run_statevector,
                    {**request, "debug": {"enabled": True}},
                ),
            ]
            for round_number in range(9):
                for label, run, data in (
                    runs[round_number % 3 :] + runs[: round_number % 3]
                ):
                    start = time.perf_counter()
                    run(data)
                    times[label].append(time.perf_counter() - start)
            medians = {key: statistics.median(values) for key, values in times.items()}
            print(
                name,
                {k: round(v, 6) for k, v in medians.items()},
                "disabled/baseline=",
                round(medians["disabled"] / medians["phase2"], 3),
            )


if __name__ == "__main__":
    main()
