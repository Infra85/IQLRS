import asyncio

import httpx

from app.main import app

SIMULATE = "/api/circuits/simulate"


def _simulate(payload: dict) -> dict:
    response = _request("POST", SIMULATE, json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _request(method: str, path: str, **kwargs) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def _amp(pair: list[float]) -> complex:
    return complex(pair[0], pair[1])


def test_empty_one_qubit_circuit():
    data = _simulate({"gates": [], "num_qubits": 1, "shots": 256, "backend": "qiskit"})
    assert data["counts"] == {"0": 256}
    assert abs(_amp(data["statevector"][0]) - 1) < 1e-9
    assert abs(_amp(data["statevector"][1])) < 1e-9
    assert data["circuit_diagram"]


def test_hadamard_one_qubit():
    data = _simulate(
        {
            "gates": [{"type": "H", "qubit": 0}],
            "num_qubits": 1,
            "shots": 2048,
            "backend": "qiskit",
        }
    )
    sv = data["statevector"]
    assert abs(abs(_amp(sv[0])) - 2**-0.5) < 1e-6
    assert abs(abs(_amp(sv[1])) - 2**-0.5) < 1e-6
    total = sum(data["counts"].values())
    assert total == 2048
    assert data["counts"].get("0", 0) > 2048 * 0.2
    assert data["counts"].get("1", 0) > 2048 * 0.2


def test_x_one_qubit():
    data = _simulate(
        {
            "gates": [{"type": "X", "qubit": 0}],
            "num_qubits": 1,
            "shots": 128,
            "backend": "qiskit",
        }
    )
    assert data["counts"] == {"1": 128}
    assert abs(_amp(data["statevector"][0])) < 1e-9
    assert abs(_amp(data["statevector"][1]) - 1) < 1e-9


def test_bell_state():
    data = _simulate(
        {
            "gates": [
                {"type": "H", "qubit": 0},
                {"type": "CNOT", "control": 0, "target": 1},
            ],
            "num_qubits": 2,
            "shots": 2048,
            "backend": "qiskit",
        }
    )
    sv = [_amp(pair) for pair in data["statevector"]]
    assert abs(abs(sv[0]) - 2**-0.5) < 1e-6
    assert abs(sv[1]) < 1e-6
    assert abs(sv[2]) < 1e-6
    assert abs(abs(sv[3]) - 2**-0.5) < 1e-6

    counts = data["counts"]
    assert sum(counts.values()) == 2048
    assert counts.get("00", 0) + counts.get("11", 0) == 2048
    assert counts.get("00", 0) > 2048 * 0.2
    assert counts.get("11", 0) > 2048 * 0.2
    assert "01" not in counts or counts["01"] == 0
    assert "10" not in counts or counts["10"] == 0


def test_y_and_z_gates_run():
    data = _simulate(
        {
            "gates": [
                {"type": "Y", "qubit": 0},
                {"type": "Z", "qubit": 0},
            ],
            "num_qubits": 1,
            "shots": 64,
            "backend": "qiskit",
        }
    )
    # Y|0> = i|1>, then Z|1> = -|1>, so Z Y |0> = -i|1>
    assert abs(_amp(data["statevector"][0])) < 1e-9
    assert abs(_amp(data["statevector"][1]) - complex(0, -1)) < 1e-6
    assert data["counts"] == {"1": 64}


def test_identity_gate():
    data = _simulate(
        {
            "gates": [{"type": "I", "qubit": 0}],
            "num_qubits": 1,
            "shots": 32,
            "backend": "qiskit",
        }
    )
    assert data["counts"] == {"0": 32}


def test_unknown_gate_rejected():
    response = _request(
        "POST",
        SIMULATE,
        json={
            "gates": [{"type": "RX", "qubit": 0}],
            "num_qubits": 1,
            "backend": "qiskit",
        },
    )
    assert response.status_code == 400


def test_unsupported_backend_rejected():
    response = _request(
        "POST",
        SIMULATE,
        json={"gates": [], "num_qubits": 1, "backend": "cirq"},
    )
    assert response.status_code == 400
