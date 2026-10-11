"""Curriculum-owned execution definitions and deterministic educational checks.

No gate semantics live here. All quantum execution delegates to Simulator V2.
"""

import json
import math
import logging
from pathlib import Path
from app.schemas.learning_challenge import ChallengeDefinition, VALIDATORS
from app.services.curriculum import MODULES
from app.services.simulators.engine import validate_and_normalize_gates, run_statevector
from app.services.simulators.qiskit_runner import run_circuit


def canonical(gates, n, registers=None):
    return validate_and_normalize_gates(
        dict(gates=gates, num_qubits=n, classical_registers=registers)
    )


def load_definitions():
    activities = {
        a["id"]: a for m in MODULES for a in m["experiments"] + m["challenges"]
    }
    definitions = {}
    for raw in json.loads(
        (Path(__file__).resolve().parents[2] / "data/challenges.json").read_text()
    ):
        definition = ChallengeDefinition.model_validate(raw)
        a = activities.get(definition.id)
        if (
            not a
            or a["moduleId"] != definition.moduleId
            or definition.id in definitions
        ):
            raise ValueError("Invalid activity identity")
        if (
            definition.objective != a["objective"]
            or definition.kind != a["type"]
            or definition.title != a["title"]
            or definition.difficulty != a["difficulty"]
        ):
            raise ValueError("Activity disagrees with Phase 1 contract")
        d = definition.model_dump(mode="json", exclude_none=True)
        c = d["starterCircuit"]
        n = c["num_qubits"]
        canonical(c["gates"], n, c.get("classical_registers"))
        for r in d["rules"]:
            if r["type"] not in VALIDATORS:
                raise ValueError("Unregistered validator")
            canonical(r["prefix"], n, c.get("classical_registers"))
            canonical(r["required"], n, c.get("classical_registers"))
            target = r.get("target")
            if r["type"] == "state_equivalence":
                if (
                    not isinstance(target, list)
                    or len(target) != 2**n
                    or any(len(z) != 2 for z in target)
                    or not math.isclose(
                        sum(abs(complex(*z)) ** 2 for z in target), 1, abs_tol=1e-8
                    )
                ):
                    raise ValueError("Invalid state target")
            if r["type"] in {"probability", "correlation", "classical_output"}:
                if (
                    not isinstance(target, dict)
                    or not target
                    or any(
                        not set(k) <= set("01")
                        or not k
                        or not math.isfinite(v)
                        or v < 0
                        or v > 1
                        for k, v in target.items()
                    )
                    or not math.isclose(sum(target.values()), 1, abs_tol=1e-8)
                ):
                    raise ValueError("Invalid probability target")
                width = (
                    sum(x["size"] for x in c.get("classical_registers", []))
                    if r["type"] == "classical_output"
                    else n
                )
                if any(len(k) != width for k in target):
                    raise ValueError("Target bit width mismatch")
            if r["type"] == "conceptual" and (
                not isinstance(target, dict) or not target
            ):
                raise ValueError("Missing conceptual target")
        p = d["prediction"]
        if (
            set(p["labels"]) != set(p["displayLabels"])
            or set(p["labels"]) != set(p["expected"])
            or len(p["labels"]) != len(set(p["labels"]))
        ):
            raise ValueError("Invalid prediction labels")
        definitions[d["id"]] = d
    if set(definitions) != set(activities):
        raise ValueError("Every curriculum activity needs an execution definition")
    return definitions


try:
    DEFINITIONS = load_definitions()
except Exception:
    logging.getLogger(__name__).exception("challenge_configuration_failure")
    raise
ALIASES = {"bell": "m4-challenge", "grover": "m6-challenge"}


def public_definition(d):
    return {
        k: v
        for k, v in d.items()
        if k
        not in {
            "rules",
            "hints",
            "successFeedback",
            "failureFeedback",
            "solutionExplanation",
            "prediction",
        }
    } | {
        "validationTypes": [r["type"] for r in d["rules"]],
        "hintsAvailable": len(d["hints"]),
        "prediction": {k: v for k, v in d["prediction"].items() if k != "expected"},
    }


def prediction_valid(d, prediction):
    if set(prediction) != set(d["prediction"]["labels"]):
        return False
    if d["prediction"]["kind"] == "distribution":
        return all(0 <= v <= 1 for v in prediction.values()) and math.isclose(
            sum(prediction.values()), 1, abs_tol=1e-6
        )
    return all(float(v).is_integer() and abs(v) <= 100000 for v in prediction.values())


def probabilities(vector):
    if not isinstance(vector, list) or not vector or len(vector) & (len(vector) - 1):
        raise ValueError("Malformed statevector")
    if any(
        not isinstance(z, list)
        or len(z) != 2
        or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in z)
        for z in vector
    ):
        raise ValueError("Malformed amplitude")
    values = [abs(complex(*z)) ** 2 for z in vector]
    if not math.isclose(sum(values), 1, abs_tol=1e-7):
        raise ValueError("Unnormalized state")
    n = (len(vector) - 1).bit_length()
    return {format(i, f"0{n}b"): v for i, v in enumerate(values)}


def matches(actual, expected, tolerance):
    if (
        not isinstance(actual, dict)
        or not actual
        or any(
            not isinstance(v, (float, int)) or not math.isfinite(v) or v < 0
            for v in actual.values()
        )
    ):
        return False
    if not math.isclose(sum(actual.values()), 1, abs_tol=1e-7):
        return False
    return all(
        abs(actual.get(k, 0) - expected.get(k, 0)) <= tolerance + 1e-12
        for k in actual.keys() | expected.keys()
    )


def fidelity(vector, target):
    probabilities(vector)
    probabilities(target)
    if len(vector) != len(target):
        return 0
    return (
        abs(sum(complex(*a).conjugate() * complex(*b) for a, b in zip(target, vector)))
        ** 2
    )


def sample_probabilities(counts):
    if (
        not isinstance(counts, dict)
        or not counts
        or any(type(v) is not int or v < 0 for v in counts.values())
        or sum(counts.values()) <= 0
    ):
        raise ValueError("Malformed counts")
    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()}


def execute(circuit):
    """One normal run; terminal measurement preparation gets a 1-shot ideal probe.

    Never interpret a collapsed dynamic trajectory as ensemble probabilities.
    """
    result = run_circuit(circuit)
    normalized = canonical(
        circuit["gates"], circuit["num_qubits"], circuit.get("classical_registers")
    )
    ideal = None
    if result["metadata"]["statevector_scope"] == "unitary":
        ideal = probabilities(result["statevector"])
    else:
        first = next(
            (
                i
                for i, g in enumerate(normalized)
                if g["type"] in {"MEASURE", "MEASURE_ALL", "RESET"}
            ),
            len(normalized),
        )
        suffix = normalized[first:]
        if (
            suffix
            and all(
                g["type"] in {"MEASURE", "MEASURE_ALL"} and not g["condition"]
                for g in suffix
            )
            and not any(g["condition"] for g in normalized[:first])
        ):
            before = run_circuit(
                {**circuit, "gates": circuit["gates"][:first], "shots": 1}
            )
            quantum = probabilities(before["statevector"])
            if result["metadata"]["counts_kind"] == "classical":
                mapping = {
                    (ref["register"], ref["bit"]): q
                    for g in suffix
                    for q, ref in zip(g["targets"], g["destinations"])
                }
                ideal = {}
                for label, p in quantum.items():
                    i = int(label, 2)
                    key = "".join(
                        str((i >> mapping[(ref["register"], ref["bit"])]) & 1)
                        for ref in result["classical_bit_order"]
                    )
                    ideal[key] = ideal.get(key, 0) + p
            else:
                ideal = quantum
    # Bounded original simulator fields, not an unrelated result representation.
    result.pop("shot_results", None)
    return {"simulation": result, "idealProbabilities": ideal}


def comparison(d, prediction, execution):
    if d["kind"] == "conceptual":
        expected = d["prediction"]["expected"]
        return {
            "matches": prediction == expected,
            "prediction": prediction,
            "actual": expected,
            "basis": "classical arithmetic",
            "tolerance": 0,
        }
    result = execution["simulation"]
    actual = sample_probabilities(result["counts"])
    ideal = execution["idealProbabilities"]
    # Four standard-error envelope with a conservative floor for shot comparison.
    tolerance = (
        d["prediction"]["tolerance"]
        if ideal is not None
        else max(0.03, 2 / math.sqrt(sum(result["counts"].values())))
    )
    return {
        "matches": matches(
            prediction, ideal if ideal is not None else actual, tolerance
        ),
        "prediction": prediction,
        "actual": actual,
        "ideal": ideal,
        "basis": "ideal probabilities" if ideal is not None else "sampled shots",
        "tolerance": tolerance,
    }


def constraints(rule, circuit, normalized):
    n = circuit["num_qubits"]
    regs = circuit.get("classical_registers")
    try:
        prefix = canonical(rule.get("prefix", []), n, regs)
        required = canonical(rule.get("required", []), n, regs)
    except ValueError:
        # A valid learner circuit can omit/rename memory required by the scaffold.
        # That misses the objective; it is not a validator service failure.
        return False

    # classical_mode is an execution marker, not operation identity.
    def clean(g):
        return {k: v for k, v in g.items() if k != "classical_mode"}

    actual = [clean(g) for g in normalized]
    return (
        len(actual) <= rule.get("maxGates", 64)
        and all(clean(g) in actual for g in required)
        and actual[: len(prefix)] == [clean(g) for g in prefix]
        and (
            not rule.get("allowed")
            or all(g["type"] in rule["allowed"] for g in normalized)
        )
    )


class BranchRandom:
    """Force each of the two equiprobable Alice outcomes via the engine RNG seam."""

    def __init__(self, bits):
        self.values = iter([0.999999999999 if b else 0.0 for b in bits])

    def random(self):
        return next(self.values)


def teleportation(rule, circuit, normalized):
    n = circuit["num_qubits"]
    regs = circuit.get("classical_registers")
    if regs != [{"name": "c", "size": 2}]:
        return False
    prefix = canonical(rule["prefix"], n, regs)
    if normalized[: len(prefix)] != prefix:
        return False
    tail = normalized[len(prefix) :]
    if (
        not tail
        or len(tail) > 8
        or any(
            g["type"] not in {"X", "Z"}
            or g["targets"] != [2]
            or g["controls"]
            or not g["condition"]
            or g["condition"]["register"] != "c"
            or g["condition"].get("bit") not in [0, 1]
            for g in tail
        )
    ):
        return False
    for preparation in [
        rule["prefix"][:2],
        [{"type": "I", "qubit": 0}],
        [{"type": "H", "qubit": 0}, {"type": "S", "qubit": 0}],
    ]:
        target = run_circuit({"num_qubits": 1, "gates": preparation, "shots": 1})[
            "statevector"
        ]
        gs = preparation + rule["prefix"][2:] + circuit["gates"][len(prefix) :]
        for c0, c1 in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            out = run_statevector(
                {**circuit, "gates": gs, "shots": 1}, rng=BranchRandom([c0, c1])
            )
            v = [complex(*z) for z in out["statevector"]]
            t = [complex(*z) for z in target]
            # Reduced-state overlap of Bob q2 with the original input; Alice is traced out.
            f = sum(
                abs(t[0].conjugate() * v[a] + t[1].conjugate() * v[a + 4]) ** 2
                for a in range(4)
            )
            if f < 1 - rule["tolerance"]:
                return False
    return True


def validate(d, circuit, prediction, execution, hints_used):
    checks = []

    def check(id, passed, message):
        checks.append({"id": id, "passed": bool(passed), "message": message})

    normalized = canonical(
        circuit["gates"], circuit["num_qubits"], circuit.get("classical_registers")
    )
    correct_qubits = circuit["num_qubits"] == d["starterCircuit"]["num_qubits"]
    if d["kind"] == "circuit":
        check(
            "qubit_count", correct_qubits, "Use the activity’s stated number of qubits."
        )
    for i, r in enumerate(d["rules"]):
        kind = r["type"]
        ok = False
        if kind == "conceptual":
            ok = prediction == r["target"]
        elif correct_qubits:
            result = execution["simulation"]
            if kind == "constraints":
                ok = constraints(r, circuit, normalized)
            elif kind == "state_equivalence":
                ok = (
                    result["metadata"]["statevector_scope"] == "unitary"
                    and fidelity(result["statevector"], r["target"])
                    >= 1 - r["tolerance"]
                )
            elif kind in {"probability", "correlation"}:
                ok = matches(
                    execution["idealProbabilities"], r["target"], r["tolerance"]
                )
            elif kind == "classical_output":
                order = result["classical_bit_order"]
                ok = order == [
                    {"register": "c", "bit": 1},
                    {"register": "c", "bit": 0},
                ] and matches(
                    execution["idealProbabilities"], r["target"], r["tolerance"]
                )
            elif kind == "teleportation":
                ok = teleportation(r, circuit, normalized)
        check(f"{kind}:{i}", ok, r["message"])
    passed = all(c["passed"] for c in checks)
    substantive = [c for c in checks if c["id"] != "qubit_count"]
    status = (
        "success"
        if passed
        else "near_miss"
        if any(c["passed"] for c in substantive)
        else "incorrect"
    )
    return {
        "status": status,
        "passed": passed,
        "score": max(50, 100 - 10 * hints_used) if passed else 0,
        "checks": checks,
        "expectation": {"prediction": d["prediction"]["expected"], "rules": d["rules"]},
        "feedback": {
            "summary": d["successFeedback"] if passed else d["failureFeedback"],
            "details": [c["message"] for c in checks if not c["passed"]],
            "explanation": d["solutionExplanation"],
        },
        "hintsUsed": hints_used,
        "challengeId": d["id"],
        "moduleId": d["moduleId"],
        "version": d["version"],
    }
