"""Authenticated activity lifecycle. Server definitions and simulations are authority."""

import hashlib
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.rate_limit import limit_requests
from app.dependencies import get_current_user
from app.models.user import User
from app.models.learning_challenge import ChallengeWorkspace, ChallengeAttempt
from app.schemas.learning_challenge import (
    CommitPrediction,
    RevisionRequest,
    StrictModel,
    ValidationResult,
)
from app.services.learning_challenges import (
    DEFINITIONS,
    ALIASES,
    public_definition,
    prediction_valid,
    canonical,
    execute,
    comparison,
    validate,
)

log = logging.getLogger(__name__)
router = APIRouter(
    prefix="/api/challenges",
    tags=["Learning activities"],
    dependencies=[Depends(get_current_user)],
)


class HintRequest(StrictModel):
    module_id: int
    version: int
    index: int = Field(ge=1, le=5)


def definition(id, module_id=None, version=None):
    d = DEFINITIONS.get(ALIASES.get(id, id))
    if not d:
        raise HTTPException(404, "Learning activity not found.")
    if module_id is not None and module_id != d["moduleId"]:
        raise HTTPException(422, "This activity does not belong to that module.")
    if version is not None and version != d["version"]:
        raise HTTPException(
            409, "This activity has been updated. Reload it before continuing."
        )
    return d


def lock(db, user):
    db.query(User).filter_by(user_id=user.user_id).with_for_update().one()


def workspace(db, user, d):
    return (
        db.query(ChallengeWorkspace)
        .filter_by(user_id=user.user_id, challenge_id=d["id"])
        .first()
    )


def attempts(db, user, d):
    return db.query(ChallengeAttempt).filter_by(
        user_id=user.user_id, challenge_id=d["id"]
    )


def view_attempt(a, full=False):
    data = {
        "id": str(a.id),
        "number": a.number,
        "hintsUsed": a.hints_used,
        "score": a.score,
        "passed": a.passed,
        "status": a.result["status"],
        "createdAt": a.created_at.isoformat(),
        "version": a.version,
    }
    if full:
        data.update(
            circuit=a.circuit,
            prediction=a.prediction,
            simulation=a.simulation,
            result=a.result,
        )
    return data


def save(db, d):
    try:
        db.commit()
    except Exception:
        db.rollback()
        log.exception("challenge_persistence_failure", extra={"challenge_id": d["id"]})
        raise HTTPException(
            503, "Your activity could not be saved. Please retry."
        ) from None


@router.get("")
def inventory(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(ChallengeAttempt).filter_by(user_id=user.user_id, passed=True).all()
    best = {}
    for r in rows:
        best[r.challenge_id] = max(best.get(r.challenge_id, 0), r.score)
    return {
        "activities": [
            {
                "id": d["id"],
                "moduleId": d["moduleId"],
                "title": d["title"],
                "kind": d["kind"],
                "version": d["version"],
                "completed": d["id"] in best,
                "bestScore": best.get(d["id"], 0),
            }
            for d in DEFINITIONS.values()
        ]
    }


@router.get("/{id}")
def detail(
    id: str,
    module: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    d = definition(id, module)
    w = workspace(db, user, d)
    rows = attempts(db, user, d).order_by(ChallengeAttempt.number.desc()).all()
    current = w and w.version == d["version"]
    return {
        "definition": public_definition(d),
        "completed": any(a.passed for a in rows),
        "bestScore": max((a.score for a in rows), default=0),
        "history": [view_attempt(a) for a in rows],
        "hints": d["hints"][: w.hints_used] if w else [],
        "workspace": {
            "revision": str(w.revision),
            "circuit": w.circuit,
            "prediction": w.prediction,
            "execution": w.execution,
            "feedback": next((a.result for a in rows if a.revision == w.revision), None),
            "comparison": comparison(d, w.prediction, w.execution)
            if w.execution
            else None,
        }
        if current
        else None,
    }


@router.put(
    "/{id}/prediction", dependencies=[Depends(limit_requests("challenge-write", 60))]
)
def commit_prediction(
    id: str,
    payload: CommitPrediction,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    d = definition(id, payload.module_id, payload.version)
    if not prediction_valid(d, payload.prediction):
        raise HTTPException(
            422,
            "Enter all prediction values. Probabilities must be between 0 and 1 and sum to 1.",
        )
    c = payload.circuit.model_dump(mode="json", exclude_none=True)
    try:
        canonical(c["gates"], c["num_qubits"], c.get("classical_registers"))
    except ValueError:
        log.info("challenge_invalid_circuit", extra={"challenge_id": d["id"]})
        raise HTTPException(
            422,
            "Invalid circuit. Check gates, qubit indices and classical destinations.",
        ) from None
    fp = hashlib.sha256(
        json.dumps(
            {
                "circuit": c,
                "prediction": payload.prediction,
                "version": payload.version,
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    lock(db, user)
    w = workspace(db, user, d)
    existing = attempts(db, user, d).filter_by(revision=payload.revision).first()
    if existing and (not w or w.revision != payload.revision):
        raise HTTPException(
            409, "This prediction was already submitted. Start a new retry."
        )
    if w and w.revision == payload.revision:
        if w.fingerprint != fp:
            raise HTTPException(
                409,
                "A committed prediction cannot change. Commit a new prediction for this circuit.",
            )
        return {"revision": str(w.revision)}
    if not w:
        w = ChallengeWorkspace(user_id=user.user_id, challenge_id=d["id"])
        db.add(w)
    w.revision = payload.revision
    w.version = d["version"]
    w.fingerprint = fp
    w.circuit = c
    w.prediction = payload.prediction
    w.execution = None
    w.updated_at = datetime.now(timezone.utc)
    save(db, d)
    return {"revision": str(w.revision)}


def current_workspace(db, user, d, payload):
    lock(db, user)
    w = workspace(db, user, d)
    if not w or w.revision != payload.revision or w.version != d["version"]:
        raise HTTPException(
            409, "Commit a prediction for the current circuit before continuing."
        )
    return w


@router.post(
    "/{id}/run", dependencies=[Depends(limit_requests("challenge-execute", 30))]
)
def run(
    id: str,
    payload: RevisionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    d = definition(id, payload.module_id, payload.version)
    w = current_workspace(db, user, d, payload)
    if d["kind"] == "conceptual":
        raise HTTPException(
            422,
            "This conceptual activity does not execute a circuit. Validate your reasoning instead.",
        )
    if w.execution is None:
        try:
            w.execution = execute(w.circuit)
        except ValueError:
            log.info("challenge_simulation_rejected", extra={"challenge_id": d["id"]})
            raise HTTPException(
                422,
                "This circuit cannot run. Check its operations and reduce its size.",
            ) from None
        except Exception:
            log.exception(
                "challenge_simulation_failure", extra={"challenge_id": d["id"]}
            )
            raise HTTPException(
                503,
                "Simulation is temporarily unavailable. Your prediction is saved; retry Run.",
            ) from None
        save(db, d)
    return {**w.execution, "comparison": comparison(d, w.prediction, w.execution)}


@router.post(
    "/{id}/hints", dependencies=[Depends(limit_requests("challenge-write", 60))]
)
def hint(
    id: str,
    payload: HintRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    d = definition(id, payload.module_id, payload.version)
    lock(db, user)
    w = workspace(db, user, d)
    if not w:
        raise HTTPException(
            409, "Commit a prediction first so your hint use can be saved."
        )
    if payload.index > len(d["hints"]) or payload.index > w.hints_used + 1:
        raise HTTPException(422, "Reveal hints one at a time.")
    w.hints_used = max(w.hints_used, payload.index)
    save(db, d)
    return {"hints": d["hints"][: w.hints_used]}


@router.post(
    "/{id}/validate", dependencies=[Depends(limit_requests("challenge-execute", 30))]
)
def submit(
    id: str,
    payload: RevisionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    d = definition(id, payload.module_id, payload.version)
    lock(db, user)
    old = attempts(db, user, d).filter_by(revision=payload.revision).first()
    if old:
        if old.version != payload.version:
            raise HTTPException(409, "This attempt belongs to an older activity version. Start a new retry.")
        return {
            "result": old.result,
            "attempt": view_attempt(old),
            "completed": any(a.passed for a in attempts(db, user, d).all()),
            "comparison": comparison(
                d,
                old.prediction,
                {
                    "simulation": old.simulation,
                    "idealProbabilities": old.simulation["idealProbabilities"],
                }
                if old.simulation
                else None,
            ),
        }
    w = current_workspace(db, user, d, payload)
    if d["kind"] == "circuit" and not w.execution:
        raise HTTPException(409, "Run the committed circuit before validating it.")
    count = attempts(db, user, d).count()
    if count >= 200:
        raise HTTPException(
            409,
            "This activity has reached its 200 saved-attempt limit. You can still experiment with Run.",
        )
    try:
        result = ValidationResult.model_validate(
            validate(d, w.circuit, w.prediction, w.execution, w.hints_used)
        ).model_dump()
    except Exception:
        log.exception(
            "challenge_validation_failure",
            extra={"challenge_id": d["id"], "version": d["version"]},
        )
        raise HTTPException(
            503,
            "Validation is temporarily unavailable. Your work is saved; please retry.",
        ) from None
    if not result["passed"]:
        log.info(
            "challenge_objective_not_met",
            extra={
                "challenge_id": d["id"],
                "checks": [x["id"] for x in result["checks"] if not x["passed"]],
            },
        )
    sim = w.execution["simulation"] if w.execution else None
    summary = (
        {
            k: sim[k]
            for k in ["counts", "classical_counts", "classical_bit_order", "metadata"]
        }
        if sim
        else None
    )
    if summary is not None:
        summary["idealProbabilities"] = w.execution["idealProbabilities"]
    a = ChallengeAttempt(
        user_id=user.user_id,
        challenge_id=d["id"],
        module_id=d["moduleId"],
        version=d["version"],
        revision=w.revision,
        fingerprint=w.fingerprint,
        number=count + 1,
        circuit=w.circuit,
        prediction=w.prediction,
        simulation=summary,
        result=result,
        passed=result["passed"],
        score=result["score"],
        hints_used=w.hints_used,
        completed_at=datetime.now(timezone.utc) if result["passed"] else None,
    )
    db.add(a)
    save(db, d)
    return {
        "result": result,
        "attempt": view_attempt(a),
        "completed": any(a.passed for a in attempts(db, user, d).all()),
        "comparison": comparison(d, w.prediction, w.execution),
    }


@router.get("/{id}/attempts/{number}")
def history_detail(
    id: str,
    number: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    d = definition(id)
    a = attempts(db, user, d).filter_by(number=number).first()
    if not a:
        raise HTTPException(404, "Attempt not found.")
    return view_attempt(a, True)


@router.post(
    "/{id}/save-circuit", dependencies=[Depends(limit_requests("challenge-write", 60))]
)
def save_circuit(
    id: str,
    payload: RevisionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish a trusted activity run into existing circuit/history storage, without rerunning."""
    from uuid import uuid4
    from app.models.quantum import Circuit, CircuitVersion
    from app.models.simulation import SimulationRun, SimulationResult

    d = definition(id, payload.module_id, payload.version)
    w = current_workspace(db, user, d, payload)
    if not w.execution:
        raise HTTPException(
            409, "Run the committed circuit before saving it to simulation history."
        )
    execution = w.execution
    if execution.get("savedSimulationId"):
        return {"simulation_id": execution["savedSimulationId"]}
    c = w.circuit
    r = execution["simulation"]
    now = datetime.now(timezone.utc)
    cid = uuid4()
    sid = uuid4()
    saved = Circuit(
        circuit_id=cid,
        user_id=user.user_id,
        name=d["title"],
        num_qubits=c["num_qubits"],
        num_classical_bits=sum(x["size"] for x in c.get("classical_registers", [])),
        framework="qiskit",
        circuit_data=c,
    )
    db.add(saved)
    # Flush the circuit before adding dependent records; rollback includes all rows.
    try:
        db.flush()
        db.add(
            CircuitVersion(
                circuit_id=cid,
                created_by=user.user_id,
                version_number=1,
                circuit_data=c,
            )
        )
        db.add(
            SimulationRun(
                simulation_id=sid,
                circuit_id=cid,
                user_id=user.user_id,
                backend="qiskit",
                shots=c["shots"],
                status="completed",
                started_at=now,
                completed_at=now,
            )
        )
        db.flush()
        state = {
            k: r[k]
            for k in [
                "measurements",
                "measurement_counts",
                "metadata",
                "classical_registers",
                "classical_bit_order",
                "classical_counts",
                "last_classical",
            ]
        }
        state.update(amplitudes=r["statevector"], shot_results=[])
        db.add(
            SimulationResult(
                simulation_id=sid,
                measurement_counts=r["counts"],
                probabilities={k: v / c["shots"] for k, v in r["counts"].items()},
                circuit_diagram=r["circuit_diagram"],
                state_vector=state,
            )
        )
        w.execution = {**execution, "savedSimulationId": str(sid)}
        save(db, d)
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        log.exception("challenge_circuit_save_failure", extra={"challenge_id": d["id"]})
        raise HTTPException(
            503, "Your circuit could not be saved to simulation history. Retry safely."
        ) from None
    return {"simulation_id": str(sid)}
