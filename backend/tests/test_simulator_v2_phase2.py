"""Sequential quantum/classical execution, with shot-by-shot independent oracles."""

from collections import Counter
from copy import deepcopy
import math
import random

import pytest

from app.services.simulators.engine import run_statevector

REGISTERS = [{"name": "c", "size": 2}]


def bit(index, register="c"):
    return {"register": register, "bit": index}


def condition(index=0, value=1, register="c"):
    return {"register": register, "bit": index, "operator": "eq", "value": value}


def gate(kind, q=0, **kwargs):
    return {"type": kind, "qubit": q, **kwargs}


def measure(q, c, register="c", **kwargs):
    return gate("MEASURE", q, destinations=[bit(c, register)], **kwargs)


def run(gates, *, shots=128, registers=None, n=2, **kwargs):
    return run_statevector(
        {
            "num_qubits": n,
            "gates": gates,
            "shots": shots,
            "classical_registers": registers or REGISTERS,
            "seed": 42,
            "shot_record_limit": min(shots, 256),
            **kwargs,
        }
    )


def assert_normalized(data):
    assert sum(r * r + i * i for r, i in data["statevector"]) == pytest.approx(
        1, abs=1e-12
    )
    assert sum(data["counts"].values()) == data["metadata"]["shots"]


def test_bell_joint_counts():
    data = run(
        [
            gate("H"),
            {"type": "CNOT", "control": 0, "target": 1},
            measure(0, 0),
            measure(1, 1),
        ],
        shots=256,
    )
    assert set(data["counts"]) == {"00", "11"}
    assert 95 < data["counts"]["00"] < 160
    assert data["counts"] == dict(Counter(s["outcome"] for s in data["shot_results"]))
    assert data["classical_counts"] == data["counts"]
    assert data["classical_bit_order"] == [bit(1), bit(0)]
    for shot in data["shot_results"]:
        assert shot["classical"]["c"] == shot["outcome"]
        assert shot["measurements"][0]["bits"] == shot["measurements"][1]["bits"]
    assert_normalized(data)


def test_measure_feedforward():
    data = run(
        [gate("H"), measure(0, 0), gate("X", 1, condition=condition()), measure(1, 1)]
    )
    assert set(data["counts"]) == {"00", "11"}
    for shot in data["shot_results"]:
        assert shot["measurements"][0]["bits"] == shot["measurements"][1]["bits"]
    assert_normalized(data)


def test_sequential_measurements_are_opposites_every_shot():
    data = run([gate("H"), measure(0, 0), gate("X"), measure(0, 1)])
    assert set(data["counts"]) == {"01", "10"}
    for shot in data["shot_results"]:
        first, second = shot["measurements"]
        assert first["bits"] != second["bits"]
        assert [first["operation"], second["operation"]] == [1, 3]
        assert first["destinations"] == [bit(0)]
        assert second["destinations"] == [bit(1)]
    last = data["shot_results"][-1]
    measured = int(last["measurements"][-1]["bits"])
    assert data["statevector"][measured][0] == pytest.approx(1)


@pytest.mark.parametrize("prep", [False, True])
@pytest.mark.parametrize("expected", [0, 1])
@pytest.mark.parametrize(
    "kind",
    ["X", "Y", "Z", "H", "RX", "RY", "RZ", "S", "T", "CNOT", "CZ", "SWAP", "CRX"],
)
def test_condition_wraps_all_existing_operations(kind, expected, prep):
    operation = {"type": kind}
    if kind in {"CNOT", "CZ", "CRX"}:
        operation.update(control=1, target=2)
    elif kind == "SWAP":
        operation["targets"] = [1, 2]
    else:
        operation["qubit"] = 2
    if kind in {"RX", "RY", "RZ", "CRX"}:
        operation["params"] = {"theta": 0.731}
    # Phase-sensitive superposition makes Z/S/T/RZ and controlled phases observable.
    prefix = ([gate("X")] if prep else []) + [measure(0, 0), gate("X", 1), gate("H", 2)]
    expected_state = run(
        prefix + ([operation] if int(prep) == expected else []), n=3, shots=1
    )["statevector"]
    data = run(
        prefix + [{**operation, "condition": condition(value=expected)}], n=3, shots=1
    )
    assert [complex(*a) for a in data["statevector"]] == pytest.approx(
        [complex(*a) for a in expected_state]
    )
    assert data["last_classical"]["c"] == f"0{int(prep)}"
    assert_normalized(data)


@pytest.mark.parametrize("quantum_control", [0, 1])
def test_quantum_and_classical_controls_are_distinct(quantum_control):
    data = run(
        [gate("H"), measure(0, 0)]
        + ([gate("X", 1)] if quantum_control else [])
        + [
            {"type": "CNOT", "control": 1, "target": 2, "condition": condition()},
            measure(2, 1),
        ],
        n=3,
    )
    for shot in data["shot_results"]:
        bits = shot["classical"]["c"]
        assert int(bits[0]) == int(bits[1]) * quantum_control


@pytest.mark.parametrize("value", [0, 1, 2, 3])
def test_register_equality(value):
    data = run(
        [
            gate("X"),
            {"type": "MEASURE", "targets": [0, 1], "destinations": [bit(1), bit(0)]},
            gate("X", 1, condition=condition(None, value)),
            measure(1, 0),
        ],
        shots=1,
    )
    # Before the condition c=10 (2), with deliberately reversed mapping.
    assert data["last_classical"]["c"] == ("11" if value == 2 else "10")


def test_multiple_register_order_and_mapping():
    registers = [{"name": "readout", "size": 2}, {"name": "flag", "size": 1}]
    data = run(
        [
            gate("X"),
            {
                "type": "MEASURE",
                "targets": [1, 0],
                "destinations": [bit(0, "flag"), bit(1, "readout")],
            },
            gate("X", 1, condition=condition(None, 2, "readout")),
        ],
        registers=registers,
        shots=1,
    )
    assert data["counts"] == {"10": 1}
    assert data["classical_bit_order"] == [bit(1, "readout"), bit(0, "flag")]
    assert data["last_classical"] == {"readout": "10", "flag": "0"}
    assert data["measurements"][0]["destinations"] == [
        bit(0, "flag"),
        bit(1, "readout"),
    ]
    assert data["statevector"][3] == [1, 0]


def test_partial_measurement_excludes_unmapped_bits_and_skipped_writes_are_marked():
    data = run([measure(0, 1)], registers=[{"name": "c", "size": 4}], shots=2)
    assert data["counts"] == {"0": 2}
    assert data["classical_bit_order"] == [bit(1)]
    assert data["last_classical"] == {"c": "0000"}
    data = run([measure(0, 1, condition=condition())], shots=2)
    assert data["counts"] == {"x": 2}
    assert data["measurements"] == []
    assert all(s["measurements"] == [] for s in data["shot_results"])


def test_repeated_writes_overwrite_memory_but_retain_history():
    data = run([measure(0, 0), gate("X"), measure(0, 0)], shots=1)
    assert data["counts"] == {"1": 1}
    assert [m["bits"] for m in data["shot_results"][0]["measurements"]] == ["0", "1"]


def test_reset_does_not_erase_classical_state():
    data = run(
        [
            gate("H"),
            measure(0, 0),
            gate("RESET"),
            gate("X", 1, condition=condition()),
            measure(1, 1),
        ]
    )
    assert set(data["counts"]) == {"00", "11"}
    assert data["statevector"][1] == data["statevector"][3] == [0, 0]
    last = int(data["last_classical"]["c"][0])
    assert data["statevector"][last * 2] == [1, 0]
    # The same wrapper works before/after reset and on reset itself.
    data = run(
        [
            gate("X"),
            measure(0, 0),
            gate("RESET", condition=condition()),
            gate("X", condition=condition()),
            measure(0, 1),
        ],
        shots=2,
    )
    assert data["counts"] == {"11": 2}


def test_fresh_quantum_and_classical_state_each_shot():
    data = run(
        [gate("X", 1, condition=condition()), gate("X"), measure(0, 0), measure(1, 1)]
    )
    assert data["counts"] == {"01": 128}  # leaked memory would flip q1 after shot one
    assert len({id(s["measurements"]) for s in data["shot_results"]}) == 128


def test_seed_local_reproducible_and_history_limit_does_not_change_execution():
    gates = [gate("H"), measure(0, 0), gate("H"), measure(0, 1)]
    before = random.getstate()
    first = run(gates, shots=256)
    assert first == run(gates, shots=256)
    assert before == random.getstate()
    short = run(gates, shots=256, shot_record_limit=3)
    assert short["shot_results"] == first["shot_results"][:3]
    assert short["counts"] == first["counts"]
    assert short["metadata"]["shot_records_truncated"] is True
    unseeded = [run(gates, shots=64, seed=None)["shot_results"] for _ in range(3)]
    assert unseeded[0] != unseeded[1] != unseeded[2]
    assert set(first["counts"]) == {"00", "01", "10", "11"}


def test_legacy_measurement_counts_stay_quantum_and_history_is_additive():
    data = run_statevector(
        {
            "num_qubits": 2,
            "gates": [gate("X"), gate("MEASURE"), gate("RESET")],
            "shots": 2,
            "shot_record_limit": 2,
        }
    )
    assert data["counts"] == {"00": 2}
    assert data["classical_counts"] == {"1": 2}
    assert data["classical_registers"] == REGISTERS
    assert data["measurements"] == [{"operation": 1, "qubits": [0], "bits": "1"}]
    assert data["shot_results"][0]["measurements"][0]["destinations"] == [bit(0)]
    assert data["metadata"]["counts_kind"] == "quantum"


def test_no_measurement_preserves_exact_unitary_state_and_quantum_counts():
    data = run([gate("H")], shots=128)
    assert data["metadata"]["counts_kind"] == "quantum"
    assert data["metadata"]["statevector_scope"] == "unitary"
    assert data["statevector"][0][0] == pytest.approx(2**-0.5)
    assert data["classical_counts"] == {}
    assert data["counts"] == dict(Counter(s["outcome"] for s in data["shot_results"]))


def test_per_operation_normalization_and_classical_invariants(monkeypatch):
    import app.services.simulators.engine as engine

    original = engine._execute

    def checked(state, operations, rng, classical, written):
        records = []
        assert state == [1] + [0] * (len(state) - 1)
        assert all(all(b == 0 for b in bits) for bits in classical.values())
        for operation in operations:
            before = deepcopy(classical)
            records.extend(original(state, [operation], rng, classical, written))
            assert sum(abs(a) ** 2 for a in state) == pytest.approx(1, abs=1e-12)
            assert all(
                type(b) is int and b in (0, 1)
                for bits in classical.values()
                for b in bits
            )
            if operation[1]["type"] not in {"MEASURE", "MEASURE_ALL"}:
                assert before == classical
        return records

    monkeypatch.setattr(engine, "_execute", checked)
    run(
        [
            gate("H"),
            measure(0, 0),
            gate("RY", 1, params={"theta": 0.3}, condition=condition()),
            {
                "type": "CRX",
                "control": 0,
                "target": 1,
                "params": {"theta": math.pi},
                "condition": condition(),
            },
            gate("RESET"),
            measure(1, 1),
        ]
    )


INVALID = [
    {"classical_registers": []},
    {"classical_registers": [{"name": "c", "size": 0}]},
    {"classical_registers": [{"name": "bad-name", "size": 2}]},
    {"classical_registers": [{"name": "c", "size": 1}, {"name": "c", "size": 1}]},
    {"classical_registers": [{"name": "a", "size": 32}, {"name": "b", "size": 1}]},
    {"gates": [gate("MEASURE")]},
    {"gates": [{"type": "MEASURE", "destinations": [bit(0)]}]},
    {"gates": [measure(0, 2)]},
    {"gates": [measure(0, -1)]},
    {"gates": [measure(0, 0, "missing")]},
    {"gates": [{"type": "MEASURE", "targets": [0, 1], "destinations": [bit(0)]}]},
    {"gates": [{"type": "MEASURE_ALL", "destinations": [bit(0), bit(0)]}]},
    {"gates": [gate("X", destinations=[bit(0)])]},
    *[
        {"gates": [gate("X", condition=c)]}
        for c in [
            False,
            {},
            {"register": "c", "value": 0},
            condition(4),
            condition(value=2),
            condition(value=-1),
            condition(value=True),
            condition(None, 4),
            condition(register="missing"),
            {**condition(), "operator": "ne"},
            {**condition(), "extra": 0},
        ]
    ],
    {"seed": -1},
    {"seed": True},
    {"shot_record_limit": 257},
    {"shots": 100001},
]


@pytest.mark.parametrize("overrides", INVALID)
def test_validation(overrides):
    with pytest.raises(ValueError):
        run_statevector(
            {
                "num_qubits": 2,
                "gates": [],
                "classical_registers": REGISTERS,
                **overrides,
            }
        )


def test_work_and_history_bounds():
    with pytest.raises(ValueError, match="work limit"):
        run([gate("H")], n=10, shots=100000)
    with pytest.raises(ValueError, match="history"):
        run([measure(0, 0)] * 100, shots=256)


@pytest.mark.parametrize("overrides", INVALID)
def test_api_validation(api, overrides):
    response = api[0].post(
        "/api/circuits/simulate",
        json={
            "num_qubits": 2,
            "gates": [],
            "classical_registers": REGISTERS,
            **overrides,
        },
    )
    assert response.status_code in (400, 422), response.text
    assert "detail" in response.json()


def test_authenticated_persistence(api, sessions):
    from app.models.quantum import (
        Circuit,
        CircuitVersion,
        SimulationRun,
        SimulationResult,
    )

    client, uid = api
    payload = {
        "num_qubits": 2,
        "shots": 64,
        "seed": 7,
        "shot_record_limit": 64,
        "classical_registers": REGISTERS,
        "gates": [
            gate("H"),
            measure(0, 0),
            gate("X", 1, condition=condition()),
            measure(1, 1),
        ],
    }
    response = client.post("/api/circuits/simulate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    saved = client.get("/api/circuits/runs/" + data["simulation_id"]).json()
    for field in [
        "counts",
        "classical_registers",
        "classical_bit_order",
        "classical_counts",
        "last_classical",
        "shot_results",
        "metadata",
    ]:
        assert saved[field] == data[field]
    assert saved["amplitudes"] == data["statevector"]
    with sessions() as db:
        for model in [Circuit, CircuitVersion, SimulationRun, SimulationResult]:
            assert db.query(model).count() == 1
        assert db.query(CircuitVersion).one().circuit_data["seed"] == 7
        assert db.query(Circuit).one().num_classical_bits == 2
    client.headers.pop("Authorization")
    assert client.get("/api/circuits/runs/" + data["simulation_id"]).status_code == 401
    guest = client.post("/api/circuits/simulate", json=payload).json()
    assert guest["simulation_id"] is None
    assert guest["shot_results"] == data["shot_results"]


def test_implicit_c_destinations_without_register_declarations():
    data = run_statevector(
        {"num_qubits": 1, "shots": 2, "gates": [gate("X"), measure(0, 0)]}
    )
    assert data["counts"] == {"1": 2}
    assert data["classical_registers"] == [{"name": "c", "size": 1}]
    assert data["metadata"]["counts_kind"] == "classical"


def test_measure_all_explicit_mapping_and_register_zero():
    data = run(
        [
            gate("X", 1, condition=condition(None, 0)),
            {"type": "MEASURE_ALL", "destinations": [bit(1), bit(0)]},
        ],
        shots=1,
    )
    assert data["counts"] == {"01": 1}
    assert data["measurements"][0]["destinations"] == [bit(0), bit(1)]


def test_empty_default_history_and_requested_limit_exceeds_shots():
    payload = {"num_qubits": 1, "shots": 2, "seed": 0, "gates": []}
    data = run_statevector(payload)
    assert data["shot_results"] == []
    assert data["metadata"]["shot_records_returned"] == 0
    data = run_statevector({**payload, "shot_record_limit": 256})
    assert len(data["shot_results"]) == 2
    assert data["metadata"]["shot_records_truncated"] is False


def test_historical_result_json_remains_readable(api, sessions):
    from app.models.quantum import SimulationResult

    client, _ = api
    data = client.post(
        "/api/circuits/simulate", json={"num_qubits": 1, "shots": 1, "gates": []}
    ).json()
    with sessions() as db:
        saved = db.query(SimulationResult).one()
        saved.state_vector = {"amplitudes": [[1, 0], [0, 0]]}
        db.commit()
    response = client.get("/api/circuits/runs/" + data["simulation_id"])
    assert response.status_code == 200
    assert response.json()["amplitudes"] == [[1, 0], [0, 0]]
    assert response.json()["counts"] == {"0": 1}
