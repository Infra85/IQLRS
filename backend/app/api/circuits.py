from time import perf_counter
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user, get_optional_user
from app.models.user import User
from app.models.quantum import Circuit, CircuitVersion
from app.models.simulation import SimulationRun, SimulationResult
from app.schemas.circuit import CircuitRequest, CircuitResult
from app.services.simulators.qiskit_runner import run_circuit

from app.core.rate_limit import limit_requests

router = APIRouter()


@router.post("/simulate", response_model=CircuitResult, dependencies=[Depends(limit_requests("simulate", 60))])
def simulate_circuit(circuit: CircuitRequest, user: User | None = Depends(get_optional_user), db: Session = Depends(get_db)):
    backend = circuit.backend.strip().lower()
    if backend != "qiskit":
        raise HTTPException(400, "Unsupported backend. Supported: qiskit")
    start = perf_counter()
    started = datetime.now(timezone.utc)
    try:
        result = CircuitResult(**run_circuit(circuit.model_dump()))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if user is None:
        return result
    try:
        saved = Circuit(user_id=user.user_id, name="Circuit experiment", num_qubits=circuit.num_qubits, framework=backend, circuit_data=circuit.model_dump())
        db.add(saved)
        db.flush()
        db.add(CircuitVersion(circuit_id=saved.circuit_id, created_by=user.user_id, version_number=1, circuit_data=circuit.model_dump()))
        run = SimulationRun(circuit_id=saved.circuit_id, user_id=user.user_id, backend=backend,
                            shots=circuit.shots, status="completed", execution_time_ms=int((perf_counter()-start)*1000), started_at=started, completed_at=datetime.now(timezone.utc))
        db.add(run)
        db.flush()
        db.add(SimulationResult(simulation_id=run.simulation_id, measurement_counts=result.counts,
                                probabilities={k: v/circuit.shots for k, v in result.counts.items()},
                                circuit_diagram=result.circuit_diagram, state_vector={"amplitudes": result.statevector}))
        result.simulation_id = str(run.simulation_id)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(503, "The simulation could not be saved. Please try again.") from None
    return result


@router.get("/runs/{run_id}")
def get_run(run_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run = db.query(SimulationRun).filter_by(simulation_id=run_id, user_id=user.user_id).first()
    if not run:
        raise HTTPException(404, "Simulation not found")
    result = db.query(SimulationResult).filter_by(simulation_id=run.simulation_id).one()
    version = db.query(CircuitVersion).filter_by(circuit_id=run.circuit_id).one()
    return {"id": run.simulation_id, "circuit": version.circuit_data, "backend": run.backend,
            "shots": run.shots, "created_at": run.completed_at, "counts": result.measurement_counts, "circuit_diagram": result.circuit_diagram,
            **(result.state_vector or {})}
