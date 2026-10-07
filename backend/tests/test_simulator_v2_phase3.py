"""The tracer observes real execution, without changing its results or RNG stream."""

import json
import math
import random

import pytest

from app.services.simulators import engine, tracing
from app.schemas.circuit import CircuitResult


def ref(bit):
    return {"register": "c", "bit": bit}


def g(kind, q=0, **kwargs):
    return {"type": kind, "qubit": q, **kwargs}


def m(q=0, bit=0):
    return g("MEASURE", q, destinations=[ref(bit)])


def cond(bit=0, value=1):
    return {"register": "c", "bit": bit, "operator": "eq", "value": value}


def payload(gates=None, **kwargs):
    return {
        "num_qubits": 2,
        "shots": 16,
        "seed": 42,
        "classical_registers": [{"name": "c", "size": 2}],
        "gates": gates
        if gates is not None
        else [g("H"), m(), g("X", 1, condition=cond()), m(1, 1)],
        **kwargs,
    }


def run(gates=None, **kwargs):
    data = engine.run_statevector(
        payload(gates, debug={"enabled": True, "shot_numbers": [1]}, **kwargs)
    )
    return data, data["debug"]["traces"][0]["checkpoints"]


def test_disabled_exact_results_and_no_recorder_allocations(monkeypatch):
    original = engine.run_statevector(payload())

    def forbidden(*args, **kwargs):
        raise AssertionError("disabled debugging attempted to record state")

    monkeypatch.setattr(engine, "TraceRecorder", forbidden)
    monkeypatch.setattr(engine, "condition_event", forbidden)
    monkeypatch.setattr(engine, "debug_result", forbidden)
    assert engine.run_statevector(payload(debug={"enabled": False})) == original
    assert engine.run_statevector(payload(debug=None)) == original
    assert "debug" not in original


@pytest.mark.parametrize(
    "gates",
    [
        [],
        [g("H")],
        [g("H"), m(), g("RESET")],
        [g("H"), m(), g("X", 1, condition=cond()), m(1, 1)],
    ],
)
@pytest.mark.parametrize("amplitudes", [False, True])
def test_tracing_does_not_change_simulation_or_rng(gates, amplitudes):
    request = payload(gates, shot_record_limit=16)
    before = random.getstate()
    base = engine.run_statevector(request)
    traced = engine.run_statevector(
        {
            **request,
            "debug": {
                "enabled": True,
                "shot_numbers": [1, 7, 16],
                "include_statevector": amplitudes,
            },
        }
    )
    traced.pop("debug")
    assert traced == base
    assert random.getstate() == before


def test_h_checkpoint_and_phase_information():
    data, checkpoints = run([g("H"), g("S")], shots=1)
    assert [c["kind"] for c in checkpoints] == [
        "start",
        "operation",
        "operation",
        "end",
    ]
    assert checkpoints[0]["quantum"]["probabilities"] == [1, 0, 0, 0]
    assert checkpoints[1]["quantum"]["probabilities"] == pytest.approx([0.5, 0.5, 0, 0])
    assert checkpoints[1]["quantum"]["statevector"] is None
    data = engine.run_statevector(
        payload(
            [g("H"), g("S")],
            shots=1,
            debug={"enabled": True, "include_statevector": True},
        )
    )
    amps = data["debug"]["traces"][0]["checkpoints"][2]["quantum"]["statevector"]
    assert [complex(*a) for a in amps] == pytest.approx([2**-0.5, 1j * 2**-0.5, 0, 0])
    # Terminal quantum sampling does not mutate the exposed circuit state (Phase 2).
    assert (
        data["debug"]["traces"][0]["checkpoints"][-1]["quantum"]["statevector"]
        == data["statevector"]
    )


def test_measurement_before_after_and_classical_write():
    data, checkpoints = run([g("H"), m()], shots=1)
    before, after = checkpoints[1:3]
    sample = after["samples"][0]
    assert sample["probabilities_before"] == pytest.approx([0.5, 0.5])
    assert sample["destination"] == ref(0)
    assert after["kind"] == "measurement" and after["executed"] is True
    assert before["classical"] == {"c": "00"}
    assert after["classical"]["c"] == "0" + str(sample["outcome"])
    expected = [0] * 4
    expected[sample["outcome"]] = 1
    assert after["quantum"]["probabilities"] == pytest.approx(expected)
    assert checkpoints[-1]["outcome"] == next(iter(data["counts"]))


def test_selected_shots_both_conditional_branches_and_order():
    data = engine.run_statevector(
        payload(
            shot_record_limit=16, debug={"enabled": True, "shot_numbers": [16, 1, 4, 9]}
        )
    )
    assert [s["shot"] for s in data["debug"]["traces"]] == [1, 4, 9, 16]
    matched = set()
    for trace in data["debug"]["traces"]:
        checkpoints = trace["checkpoints"]
        assert [c["operation_index"] for c in checkpoints] == [None, 0, 1, 2, 3, None]
        conditional = checkpoints[3]
        value = int(checkpoints[2]["classical"]["c"][1])
        assert conditional["condition"] == {
            "actual": value,
            "expected": 1,
            "matched": bool(value),
        }
        assert conditional["executed"] is bool(value)
        assert conditional["kind"] == "condition"
        matched.add(conditional["executed"])
        record = data["shot_results"][trace["shot"] - 1]
        assert checkpoints[-1]["outcome"] == record["outcome"]
        assert checkpoints[-1]["classical"] == record["classical"]
    assert matched == {True, False}


def test_group_measurement_probabilities_follow_actual_collapse_order():
    data, checkpoints = run(
        [
            g("H"),
            {"type": "CNOT", "control": 0, "target": 1},
            {"type": "MEASURE", "targets": [1, 0], "destinations": [ref(0), ref(1)]},
        ],
        shots=1,
    )
    samples = checkpoints[3]["samples"]
    assert [s["qubit"] for s in samples] == [1, 0]
    assert samples[0]["probabilities_before"] == pytest.approx([0.5, 0.5])
    first = samples[0]["outcome"]
    assert samples[1]["probabilities_before"] == [1 - first, first]
    assert samples[1]["outcome"] == first
    assert checkpoints[3]["classical"]["c"] == str(first) * 2


def test_sequential_opposite_measurement_and_snapshot_independence():
    _, cps = run([g("H"), m(), g("X"), m(0, 1)], shots=1)
    first, second = cps[2]["samples"][0]["outcome"], cps[4]["samples"][0]["outcome"]
    assert first != second
    assert cps[2]["quantum"]["probabilities"][first] == pytest.approx(1)
    assert cps[3]["quantum"]["probabilities"][second] == pytest.approx(1)
    assert cps[2]["classical"]["c"] == f"0{first}"
    assert cps[4]["classical"]["c"] == f"{second}{first}"
    cps[0]["quantum"]["probabilities"][0] = 99
    assert cps[-1]["quantum"]["probabilities"][0] != 99


def test_reset_keeps_classical_memory_and_records_internal_sample():
    _, cps = run([g("X"), m(), g("RESET"), g("X", 1, condition=cond())], shots=1)
    reset = cps[3]
    assert reset["kind"] == "reset"
    assert reset["samples"] == [
        {"qubit": 0, "destination": None, "outcome": 1, "probabilities_before": [0, 1]}
    ]
    assert reset["quantum"]["probabilities"] == [1, 0, 0, 0]
    assert reset["classical"] == cps[2]["classical"] == {"c": "01"}
    assert cps[4]["executed"] is True


def test_register_condition_and_skipped_measurement_reset():
    _, cps = run(
        [
            g("X", 1, condition=cond(None, 0)),
            {**m(), "condition": cond(None, 3)},
            g("RESET", 1, condition=cond()),
        ],
        shots=1,
    )
    assert cps[1]["condition"] == {"actual": 0, "expected": 0, "matched": True}
    for cp in cps[2:4]:
        assert cp["kind"] == "condition"
        assert cp["executed"] is False
        assert cp["samples"] == []
        assert cp["classical"] == {"c": "00"}
        assert cp["quantum"]["probabilities"] == [0, 0, 1, 0]


def test_condition_read_before_conditional_measurement_overwrites_memory():
    _, cps = run([g("X"), {**m(), "condition": cond(value=0)}], shots=1)
    assert cps[2]["condition"]["actual"] == 0
    assert cps[2]["condition"]["matched"] is True
    assert cps[2]["classical"]["c"] == "01"
    assert cps[2]["kind"] == "measurement"


def test_selected_mode_always_includes_stochastic_and_conditional_events():
    gates = [g("H"), g("I"), m(), g("X", 1, condition=cond()), g("RESET")]
    data = engine.run_statevector(
        payload(
            gates,
            debug={
                "enabled": True,
                "checkpoint_mode": "selected",
                "operation_indices": [0],
            },
        )
    )
    cps = data["debug"]["traces"][0]["checkpoints"]
    assert [c["operation_index"] for c in cps] == [None, 0, 2, 3, 4, None]
    assert set(data["debug"]["operations"]) == {"0", "2", "3", "4"}
    assert data["debug"]["operations"]["3"]["condition"] == cond()
    assert "gates" not in cps[1] and "operation" not in cps[1]


def test_trace_normalization_for_parameterized_controlled_and_reset():
    gates = [
        g("H"),
        g("RY", 1, params={"theta": 0.71}),
        {"type": "CRX", "control": 0, "target": 1, "params": {"theta": math.pi / 2}},
        {"type": "SWAP", "targets": [1, 0]},
        m(),
        g("RESET", 1),
    ]
    data = engine.run_statevector(
        payload(
            gates,
            debug={
                "enabled": True,
                "shot_numbers": [1, 2],
                "include_statevector": True,
            },
        )
    )
    for trace in data["debug"]["traces"]:
        for cp in trace["checkpoints"]:
            assert sum(cp["quantum"]["probabilities"]) == pytest.approx(1, abs=1e-12)
            assert [
                r * r + i * i for r, i in cp["quantum"]["statevector"]
            ] == pytest.approx(cp["quantum"]["probabilities"])


INVALID_DEBUG = [
    True,
    [],
    {"enabled": "true"},
    {"enabled": True, "shot_numbers": []},
    {"enabled": True, "shot_numbers": list(range(1, 18))},
    *[{"enabled": True, "shot_numbers": [v]} for v in [0, -1, 17, True, 0.5, "1"]],
    {"enabled": True, "shot_numbers": [1, 1]},
    {"enabled": True, "checkpoint_mode": "infinite"},
    {"enabled": True, "operation_indices": [0]},
    *[
        {"enabled": True, "checkpoint_mode": "selected", "operation_indices": v}
        for v in [None, [], [-1], [4], [True], [0, 0], [0] * 255]
    ],
    {"enabled": True, "include_statevector": 1},
    {"enabled": True, "max_checkpoints": 999999},
    {"enabled": False, "shot_numbers": list(range(1, 18))},
]


@pytest.mark.parametrize("debug", INVALID_DEBUG)
def test_invalid_debug(debug):
    with pytest.raises(ValueError):
        engine.run_statevector(payload(debug=debug))


def test_all_structural_limits_and_no_partial_trace_truncation():
    with pytest.raises(ValueError, match="256 checkpoints"):
        engine.run_statevector(
            payload([g("I")] * 255, shots=1, debug={"enabled": True})
        )
    with pytest.raises(ValueError, match="512 total"):
        engine.run_statevector(
            payload(
                [g("I")] * 31,
                debug={"enabled": True, "shot_numbers": list(range(1, 17))},
            )
        )
    with pytest.raises(ValueError, match="32768"):
        engine.run_statevector(
            payload([g("I")] * 31, num_qubits=10, shots=1, debug={"enabled": True})
        )
    with pytest.raises(ValueError, match="64 statevector"):
        engine.run_statevector(
            payload(
                [g("I")] * 63,
                shots=1,
                debug={"enabled": True, "include_statevector": True},
            )
        )
    # Mandatory skipped conditions cannot bypass per-shot limits via selected mode.
    with pytest.raises(ValueError, match="256 checkpoints"):
        engine.run_statevector(
            payload(
                [g("I", condition=cond())] * 255,
                shots=1,
                debug={
                    "enabled": True,
                    "checkpoint_mode": "selected",
                    "operation_indices": [0],
                },
            )
        )


def test_limits_are_enforced_before_execution(monkeypatch):
    monkeypatch.setattr(
        engine, "_execute", lambda *a: pytest.fail("executed before debug validation")
    )
    with pytest.raises(ValueError):
        engine.run_statevector(payload(debug={"enabled": True, "shot_numbers": [100]}))


def test_exact_limit_requests_and_serialized_budget():
    requests = [
        payload([g("I")] * 254, shots=1, debug={"enabled": True}),
        payload(
            [g("I")] * 30, debug={"enabled": True, "shot_numbers": list(range(1, 17))}
        ),
        payload([g("I")] * 30, num_qubits=10, shots=1, debug={"enabled": True}),
        payload(
            [g("I")] * 62, shots=1, debug={"enabled": True, "include_statevector": True}
        ),
    ]
    for request in requests:
        result = engine.run_statevector(request)
        debug = CircuitResult(**result).model_dump()["debug"]
        assert (
            len(json.dumps(debug, separators=(",", ":")).encode())
            <= tracing.MAX_DEBUG_BYTES
        )
        assert all(len(t["checkpoints"]) <= 256 for t in debug["traces"])


def test_byte_guard(monkeypatch):
    monkeypatch.setattr(tracing, "MAX_DEBUG_BYTES", 100)
    with pytest.raises(ValueError, match="2000000 bytes"):
        run()


def test_only_selected_shots_recorded_and_late_shot_matches(monkeypatch):
    observed = []
    recorder = engine.TraceRecorder

    def counted(*args):
        observed.append(True)
        return recorder(*args)

    monkeypatch.setattr(engine, "TraceRecorder", counted)
    request = payload(
        shots=100, shot_record_limit=100, debug={"enabled": True, "shot_numbers": [100]}
    )
    result = engine.run_statevector(request)
    assert len(observed) == 1
    trace = result["debug"]["traces"][0]
    assert trace["shot"] == 100
    assert (
        trace["checkpoints"][-1]["classical"] == result["shot_results"][99]["classical"]
    )
    assert trace["checkpoints"][-1]["outcome"] == result["shot_results"][99]["outcome"]


@pytest.mark.parametrize("debug", INVALID_DEBUG)
def test_api_validation(api, debug):
    response = api[0].post("/api/circuits/simulate", json=payload(debug=debug))
    assert response.status_code in (400, 422), response.text
    assert "detail" in response.json()


def test_trace_response_is_ephemeral_and_authenticated_persistence_unchanged(
    api, sessions
):
    from app.models.quantum import (
        Circuit,
        CircuitVersion,
        SimulationRun,
        SimulationResult,
    )

    client, _ = api
    request = payload(
        debug={"enabled": True, "shot_numbers": [1, 16]}, shot_record_limit=16
    )
    response = client.post("/api/circuits/simulate", json=request)
    assert response.status_code == 200, response.text
    data = response.json()
    assert [t["shot"] for t in data["debug"]["traces"]] == [1, 16]
    saved = client.get("/api/circuits/runs/" + data["simulation_id"]).json()
    assert saved["counts"] == data["counts"]
    assert saved["shot_results"] == data["shot_results"]
    assert "debug" not in saved
    with sessions() as db:
        for model in [Circuit, CircuitVersion, SimulationRun, SimulationResult]:
            assert db.query(model).count() == 1
        assert "debug" not in db.query(SimulationResult).one().state_vector
    client.headers.pop("Authorization")
    assert client.get("/api/circuits/runs/" + data["simulation_id"]).status_code == 401
    guest = client.post("/api/circuits/simulate", json=request)
    assert guest.status_code == 200
    assert guest.json()["debug"] == data["debug"]
    assert guest.json()["simulation_id"] is None
