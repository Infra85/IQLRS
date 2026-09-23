from app.services.simulators.engine import run_statevector


def _amp(pair: list[float]) -> complex:
    return complex(pair[0], pair[1])


def test_engine_empty():
    data = run_statevector({"gates": [], "num_qubits": 1, "shots": 64})
    assert data["counts"] == {"0": 64}
    assert abs(_amp(data["statevector"][0]) - 1) < 1e-9


def test_engine_h():
    data = run_statevector(
        {"gates": [{"type": "H", "qubit": 0}], "num_qubits": 1, "shots": 2048}
    )
    assert abs(abs(_amp(data["statevector"][0])) - 2**-0.5) < 1e-6
    assert abs(abs(_amp(data["statevector"][1])) - 2**-0.5) < 1e-6


def test_engine_x():
    data = run_statevector(
        {"gates": [{"type": "X", "qubit": 0}], "num_qubits": 1, "shots": 32}
    )
    assert data["counts"] == {"1": 32}


def test_engine_bell():
    data = run_statevector(
        {
            "gates": [
                {"type": "H", "qubit": 0},
                {"type": "CNOT", "control": 0, "target": 1},
            ],
            "num_qubits": 2,
            "shots": 2048,
        }
    )
    sv = [_amp(pair) for pair in data["statevector"]]
    assert abs(abs(sv[0]) - 2**-0.5) < 1e-6
    assert abs(sv[1]) < 1e-6
    assert abs(sv[2]) < 1e-6
    assert abs(abs(sv[3]) - 2**-0.5) < 1e-6
    counts = data["counts"]
    assert counts.get("00", 0) + counts.get("11", 0) == 2048
    assert counts.get("00", 0) > 400
    assert counts.get("11", 0) > 400
