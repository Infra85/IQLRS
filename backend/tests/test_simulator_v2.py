"""Analytical oracles and seeded stochastic regressions for Simulator V2."""

import cmath
import math
import random

import pytest

from app.services.simulators.engine import run_statevector
from app.services.simulators.qiskit_runner import run_circuit


def run(gates, n=1, shots=32, seed=7):
    result = run_statevector(
        dict(gates=gates, num_qubits=n, shots=shots), rng=random.Random(seed)
    )
    state = [complex(*a) for a in result["statevector"]]
    assert sum(abs(a) ** 2 for a in state) == pytest.approx(1, abs=1e-12)
    assert sum(result["counts"].values()) == shots
    return state, result


def g(kind, q=0, **kwargs):
    return dict(type=kind, qubit=q, **kwargs)


@pytest.mark.parametrize("theta", [0, math.pi, math.pi / 2, -math.pi / 2, 0.731])
@pytest.mark.parametrize("kind", ["RX", "RY", "RZ"])
@pytest.mark.parametrize("initial", [0, 1])
def test_rotations(kind, theta, initial):
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    expected = {
        "RX": [c, -1j * s] if not initial else [-1j * s, c],
        "RY": [c, s] if not initial else [-s, c],
        "RZ": [cmath.exp(-1j * theta / 2), 0]
        if not initial
        else [0, cmath.exp(1j * theta / 2)],
    }[kind]
    state, _ = run(([g("X")] if initial else []) + [g(kind, params={"theta": theta})])
    assert state == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize(
    "kind,phase",
    [
        ("S", 1j),
        ("T", cmath.exp(1j * math.pi / 4)),
        ("SDG", -1j),
        ("TDG", cmath.exp(-1j * math.pi / 4)),
    ],
)
@pytest.mark.parametrize("prep", ["I", "X", "H"])
def test_phase_gates(kind, phase, prep):
    expected = {"I": [1, 0], "X": [0, phase], "H": [2**-0.5, phase * 2**-0.5]}[prep]
    assert run([g(prep), g(kind)])[0] == pytest.approx(expected)


@pytest.mark.parametrize("a,b", [(0, 1), (0, 2), (2, 0)])
@pytest.mark.parametrize("basis", range(8))
def test_swap_basis(a, b, basis):
    gates = [g("X", q) for q in range(3) if basis & (1 << q)]
    state, result = run(gates + [dict(type="SWAP", targets=[a, b])], 3)
    expected = (
        basis ^ ((1 << a) | (1 << b))
        if bool(basis & (1 << a)) != bool(basis & (1 << b))
        else basis
    )
    assert state[expected] == 1
    assert result["counts"] == {format(expected, "03b"): 32}


def test_swap_superposition():
    state, _ = run([g("H"), g("S"), dict(type="SWAP", targets=[2, 0])], 3)
    assert state == pytest.approx([2**-0.5, 0, 0, 0, 1j * 2**-0.5, 0, 0, 0])


@pytest.mark.parametrize("kind", ["CX", "CNOT", "CY", "CZ", "CH", "CRX", "CRY", "CRZ"])
@pytest.mark.parametrize("control,target", [(0, 2), (2, 0)])
@pytest.mark.parametrize("active", [False, True])
def test_controlled_oracle(kind, control, target, active):
    theta = 0.83
    params = {"params": {"theta": theta}} if kind.startswith("CR") else {}
    # Independent analytical action on target |0>.
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    pair = (
        {
            "CX": [0, 1],
            "CNOT": [0, 1],
            "CY": [0, 1j],
            "CZ": [1, 0],
            "CH": [2**-0.5, 2**-0.5],
            "CRX": [c, -1j * s],
            "CRY": [c, s],
            "CRZ": [cmath.exp(-1j * theta / 2), 0],
        }[kind]
        if active
        else [1, 0]
    )
    prep = [g("X", control)] if active else []
    state, _ = run(
        prep + [dict(type=kind, control=control, target=target, **params)], 3
    )
    expected = [0j] * 8
    offset = (1 << control) if active else 0
    expected[offset], expected[offset | (1 << target)] = pair
    assert state == pytest.approx(expected)


@pytest.mark.parametrize("basis", range(8))
def test_cz_phase_basis(basis):
    state, _ = run(
        [g("X", q) for q in range(3) if basis & (1 << q)]
        + [dict(type="CZ", control=2, target=0)],
        3,
    )
    assert state[basis] == (-1 if basis & 5 == 5 else 1)


def test_controlled_superposition_and_multiple_controls():
    state, _ = run([g("H", 0), g("H", 2), dict(type="CZ", control=2, target=0)], 3)
    assert state == pytest.approx([0.5, 0.5, 0, 0, 0.5, -0.5, 0, 0])
    for basis in range(8):
        state, _ = run(
            [g("X", q) for q in range(3) if basis & (1 << q)]
            + [dict(type="X", controls=[0, 2], targets=[1])],
            3,
        )
        assert state[basis ^ 2 if basis & 5 == 5 else basis] == 1


@pytest.mark.parametrize("q", [0, 2])
def test_measurement_order_and_determinism(q):
    state, result = run([g("X", q), dict(type="MEASURE_ALL")], 3)
    bits = format(1 << q, "03b")
    assert result["counts"] == {bits: 32}
    assert result["measurements"] == [
        {"operation": 1, "qubits": [2, 1, 0], "bits": bits}
    ]
    assert result["measurement_counts"] == {"1": {bits: 32}}
    assert state[1 << q] == 1


def test_bell_shots_collapse_and_repeated_measurements():
    state, result = run(
        [
            g("H"),
            dict(type="CNOT", control=0, target=1),
            g("MEASURE"),
            dict(type="MEASURE_ALL"),
        ],
        2,
        shots=4000,
    )
    assert set(result["counts"]) == {"00", "11"}
    assert 1800 < result["counts"]["00"] < 2200
    first, second = result["measurements"]
    assert second["bits"] == first["bits"] * 2
    assert abs(state[int(second["bits"], 2)]) == pytest.approx(1)
    assert result["metadata"]["statevector_scope"] == "last_shot"


def test_midcircuit_measurement_is_not_terminal_sampling():
    state, result = run([g("H"), g("MEASURE"), g("X"), g("MEASURE")], shots=200)
    a, b = result["measurements"]
    assert a["bits"] != b["bits"]
    assert (
        result["measurement_counts"]["1"]["0"] == result["measurement_counts"]["3"]["1"]
    )
    assert state[int(b["bits"])] == pytest.approx(1)


@pytest.mark.parametrize("prep", [[], [g("X")], [g("H")], [g("X"), g("H")]])
def test_reset_single(prep):
    state, result = run(prep + [g("RESET")], shots=200)
    assert abs(state[0]) == pytest.approx(1)
    assert state[1] == 0
    assert result["counts"] == {"0": 200}


def test_entangled_reset_retains_conditional_partner():
    state, result = run(
        [g("H"), dict(type="CX", control=0, target=1), g("RESET")], 2, shots=4000
    )
    assert set(result["counts"]) == {"00", "10"}
    assert 1800 < result["counts"]["00"] < 2200
    assert state[1] == state[3] == 0
    assert sum(abs(a) > 0.99 for a in state) == 1


@pytest.mark.parametrize(
    "gate",
    [
        g("H", -1),
        g("X", 2),
        g("X", 0.5),
        g("X", True),
        {"type": "X"},
        {"type": "NOPE", "qubit": 0},
        "H",
        None,
        dict(type="CZ", control=0, target=0),
        dict(type="X", controls=[1, 1], targets=[0]),
        dict(type="SWAP", targets=[0]),
        g("RX"),
        g("RX", params={"theta": "pi"}),
        *[g("RY", params={"theta": v}) for v in [math.nan, math.inf, -math.inf, True]],
        g("RESET", controls=[1]),
        g("T", params={"theta": 1}),
        g("H", targets=[1]),
        dict(type="CRZ", target=0, params={"theta": 1}),
        g("X", params=[1]),
    ],
)
def test_invalid_operations(gate):
    with pytest.raises(ValueError):
        run([gate], 2)


def test_random_unitary_circuit_inverse():
    rng = random.Random(37)
    gates, inverse = [], []
    for _ in range(100):
        kind, q, theta = (
            rng.choice(["RX", "RY", "RZ"]),
            rng.randrange(4),
            rng.uniform(-20, 20),
        )
        controls = [c for c in range(4) if c != q and rng.random() < 0.3]
        gates.append(g(kind, q, controls=controls, params={"theta": theta}))
        inverse.insert(0, g(kind, q, controls=controls, params={"theta": -theta}))
    run(gates, 4)
    assert run(gates + inverse, 4)[0] == pytest.approx([1] + [0] * 15, abs=1e-12)


def test_runner_matches_engine_and_limits():
    payload = dict(
        gates=[g("RX", params={"theta": math.pi}), g("RESET")], num_qubits=1, shots=12
    )
    assert run_circuit(payload)["counts"] == {"0": 12}
    with pytest.raises(ValueError, match="work limit"):
        run([dict(type="MEASURE_ALL")], 10, 100000)


def test_v2_authenticated_roundtrip(api, sessions):
    from app.models.quantum import (
        Circuit,
        CircuitVersion,
        SimulationRun,
        SimulationResult,
    )

    client, _ = api
    gates = [
        g("RY", params={"theta": math.pi}),
        dict(type="SWAP", targets=[0, 1]),
        dict(type="CRX", control=1, target=0, params={"theta": math.pi}),
        dict(type="MEASURE_ALL"),
        g("RESET"),
    ]
    response = client.post(
        "/api/circuits/simulate", json=dict(gates=gates, num_qubits=2, shots=24)
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["counts"] == {"10": 24}
    assert data["measurement_counts"] == {"3": {"11": 24}}
    saved = client.get("/api/circuits/runs/" + data["simulation_id"]).json()
    assert saved["amplitudes"] == data["statevector"]
    assert saved["measurements"] == data["measurements"]
    assert saved["measurement_counts"] == data["measurement_counts"]
    assert saved["circuit"]["gates"][0]["params"]["theta"] == math.pi
    with sessions() as db:
        for model in [Circuit, CircuitVersion, SimulationRun, SimulationResult]:
            assert db.query(model).count() == 1


@pytest.mark.parametrize(
    "gate",
    [
        {"type": "X"},
        g("RX"),
        g("RX", params={"theta": "bad"}),
        g("X", True),
        {"type": "UNKNOWN"},
        {"type": "CZ", "control": 0, "target": 0},
        "X",
    ],
)
def test_api_validation(api, gate):
    response = api[0].post(
        "/api/circuits/simulate", json=dict(gates=[gate], num_qubits=2, shots=1)
    )
    assert response.status_code in (400, 422)
    assert "detail" in response.json()


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_api_rejects_nonfinite_json_cleanly(api, value):
    response = api[0].post(
        "/api/circuits/simulate",
        content='{"num_qubits":1,"gates":[{"type":"RX","qubit":0,"params":{"theta":'
        + value
        + "}}]}",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert "finite" in response.json()["detail"]


@pytest.mark.parametrize("theta", [1e308, -1e308])
def test_large_finite_angles_remain_normalized(theta):
    for kind in ["RX", "RY", "RZ"]:
        run([g("H"), g(kind, params={"theta": theta})])


def test_overflow_angle_is_validation_error():
    with pytest.raises(ValueError, match="finite"):
        run([g("RX", params={"theta": 10**1000})])


@pytest.mark.parametrize("kind,expected", [("CY", -1j), ("CZ", -1)])
def test_controlled_phase_on_one_target(kind, expected):
    state, _ = run([g("X", 0), g("X", 2), dict(type=kind, control=2, target=0)], 3)
    assert state[4 if kind == "CY" else 5] == expected


def test_unitary_and_stochastic_guest_paths(api):
    client, _ = api
    client.headers.pop("Authorization")
    for gates in [
        [g("RX", params={"theta": math.pi})],
        [g("X"), g("MEASURE"), g("RESET")],
    ]:
        response = client.post(
            "/api/circuits/simulate", json=dict(gates=gates, num_qubits=1, shots=2)
        )
        assert response.status_code == 200
        assert response.json()["simulation_id"] is None


@pytest.mark.parametrize("targets", [1, "0", False])
def test_malformed_swap_targets_are_validation_errors(targets):
    with pytest.raises(ValueError, match="targets must be a list"):
        run([dict(type="SWAP", control=0, targets=targets)], 2)


def test_multiple_controls_parameterized_gate():
    for basis in range(8):
        state, _ = run(
            [g("X", q) for q in range(3) if basis & (1 << q)]
            + [
                dict(type="RX", controls=[2, 0], targets=[1], params={"theta": math.pi})
            ],
            3,
        )
        active = basis & 5 == 5
        assert state[basis ^ 2 if active else basis] == pytest.approx(
            -1j if active else 1
        )
