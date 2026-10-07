"""Authenticated, bounded asynchronous QPU lifecycle; no cloud SDK calls here."""

import hashlib
import json
import logging
from datetime import timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limit_requests
from app.dependencies import get_current_user
from app.models.user import User
from app.models.hardware import HardwareJob, now
from app.schemas.hardware import HardwareRequest
from app.services.hardware import registry
from app.services.hardware.base import (
    HardwareError,
    TERMINAL,
    checked_counts,
    provider_failure,
)

router = APIRouter()
log = logging.getLogger(__name__)


def enabled():
    if not settings.hardware_execution_enabled:
        raise HTTPException(503, "Hardware execution is disabled")


def call(operation, *args):
    try:
        return operation(*args)
    except HardwareError as exc:
        raise HTTPException(400, str(exc)) from None
    except Exception as exc:
        # Type only: SDK messages and stack frames may contain bearer tokens/URLs.
        log.warning(
            "hardware_provider_error operation=%s error_type=%s",
            getattr(operation, "__name__", type(operation).__name__),
            type(exc).__name__,
        )
        status, message, _ = provider_failure(exc)
        raise HTTPException(status, message) from None


def provider(name):
    enabled()
    return call(registry.get_provider, name)


def view(job):
    return {
        "id": str(job.id),
        "execution_mode": "HARDWARE",
        "provider": job.provider,
        "provider_job_id": job.provider_job_id,
        "device_id": job.device_id,
        "status": job.status,
        "shots": job.shots,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "submitted_at": job.submitted_at,
        "completed_at": job.completed_at,
        "metadata": job.execution_metadata,
        "failure": job.failure,
        "result": job.result,
        "circuit": job.circuit,
    }


def audit(job):
    log.info(
        "hardware_job user=%s id=%s provider=%s device=%s shots=%s circuit_hash=%s provider_job=%s status=%s",
        job.user_id,
        job.id,
        job.provider,
        job.device_id,
        job.shots,
        job.fingerprint,
        job.provider_job_id,
        job.status,
    )


@router.get(
    "/providers", dependencies=[Depends(limit_requests("hardware-providers", 60))]
)
def providers():
    if not settings.hardware_execution_enabled:
        return {
            "enabled": False,
            "providers": [],
            "max_shots": settings.hardware_max_shots,
        }
    entries = []
    for name in ("ibm", "braket"):
        try:
            registry.get_provider(name)
            entries.append({"id": name, "available": True, "reason": None})
        except HardwareError as exc:
            entries.append({"id": name, "available": False, "reason": str(exc)})
    return {
        "enabled": True,
        "providers": entries,
        "max_shots": settings.hardware_max_shots,
    }


@router.get(
    "/devices", dependencies=[Depends(limit_requests("hardware-discovery", 12))]
)
def devices(
    provider_id: str,
    operational_only: bool = True,
    user: User = Depends(get_current_user),
):
    items = call(provider(provider_id).devices)
    return [
        d
        for d in items
        if not d["simulator"] and (not operational_only or d["operational"])
    ]


@router.get(
    "/devices/{provider_id}/{device_id:path}",
    dependencies=[Depends(limit_requests("hardware-discovery", 12))],
)
def device(provider_id: str, device_id: str, user: User = Depends(get_current_user)):
    return call(provider(provider_id).device, device_id)


def compile_request(body):
    enabled()
    if body.circuit.shots > settings.hardware_max_shots:
        raise HTTPException(400, "Hardware shots exceed the configured per-job limit")
    adapter = provider(body.provider)
    try:
        return adapter, call(adapter.compile, body.device_id, body.circuit.model_dump())
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from None


@router.post(
    "/jobs/validate", dependencies=[Depends(limit_requests("hardware-validation", 10))]
)
def validate(body: HardwareRequest, user: User = Depends(get_current_user)):
    try:
        _, compiled = compile_request(body)
        return {
            "valid": True,
            "unsupported_operations": [],
            "compilation": compiled.metadata,
            "qubit_requirement": body.circuit.num_qubits,
            "classical_compatible": True,
            "warnings": compiled.metadata.get("warnings", []),
        }
    except HTTPException as exc:
        if exc.status_code != 400:
            raise
        return {
            "valid": False,
            "unsupported_operations": [exc.detail],
            "warnings": [],
            "compilation": None,
            "qubit_requirement": body.circuit.num_qubits,
            "classical_compatible": False,
        }


@router.post(
    "/jobs",
    status_code=202,
    dependencies=[Depends(limit_requests("hardware-submit", 5))],
)
def submit(
    body: HardwareRequest,
    idempotency_key: str = Header(
        min_length=8, max_length=80, pattern=r"^[A-Za-z0-9_-]+$"
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enabled()
    if not body.confirmed:
        raise HTTPException(
            400, "Explicit confirmation of real QPU execution is required"
        )
    fingerprint = hashlib.sha256(
        json.dumps(body.model_dump(), sort_keys=True).encode()
    ).hexdigest()
    # Serialize reservations per owner, including across processes. Commit before provider call.
    db.query(User).filter_by(user_id=user.user_id).with_for_update().one()
    existing = (
        db.query(HardwareJob)
        .filter_by(user_id=user.user_id, idempotency_key=idempotency_key)
        .first()
    )
    if existing:
        if existing.fingerprint != fingerprint:
            raise HTTPException(
                409, "Idempotency key was already used for a different workload"
            )
        return view(existing)
    start = now().replace(hour=0, minute=0, second=0, microsecond=0)
    jobs, shots = (
        db.query(
            func.count(HardwareJob.id), func.coalesce(func.sum(HardwareJob.shots), 0)
        )
        .filter(HardwareJob.user_id == user.user_id, HardwareJob.created_at >= start)
        .one()
    )
    if (
        jobs >= settings.hardware_max_jobs_per_user_per_day
        or shots + body.circuit.shots > settings.hardware_max_shots_per_user_per_day
    ):
        raise HTTPException(429, "Daily hardware job or shot limit reached")
    adapter, compiled = compile_request(body)
    job = HardwareJob(
        user_id=user.user_id,
        idempotency_key=idempotency_key,
        fingerprint=fingerprint,
        provider=body.provider,
        device_id=body.device_id,
        shots=body.circuit.shots,
        circuit=body.circuit.model_dump(),
        execution_metadata={"compilation": compiled.metadata},
        status="UNKNOWN",
        failure="Submission is pending or uncertain; do not resubmit with a new key",
    )
    db.add(job)
    db.commit()
    audit(job)
    try:
        job.provider_job_id = adapter.submit(
            job.device_id, compiled, job.shots, str(job.id)
        )
        job.status, job.failure, job.submitted_at = "QUEUED", None, now()
    except Exception as exc:
        # The provider may have accepted the request. Never automatically retry.
        _, message, rejected = provider_failure(exc)
        if rejected:
            job.status, job.failure, job.completed_at = "FAILED", message, now()
        log.warning(
            "hardware_submission_error id=%s error_type=%s rejected=%s",
            job.id,
            type(exc).__name__,
            rejected,
        )
    job.updated_at = now()
    db.commit()
    audit(job)
    return view(job)


def owned(db, user, job_id):
    job = (
        db.query(HardwareJob)
        .filter_by(id=job_id, user_id=user.user_id)
        .with_for_update()
        .first()
    )
    if not job:
        raise HTTPException(404, "Hardware job not found")
    return job


def refresh(db, job):
    if job.status in TERMINAL or not job.provider_job_id:
        return
    if job.polled_at and now() - job.polled_at < timedelta(seconds=5):
        return
    adapter = provider(job.provider)
    update = call(adapter.status, job.provider_job_id)
    status = update["status"]
    if status == "COMPLETED":
        result = call(
            adapter.result,
            job.provider_job_id,
            job.execution_metadata["compilation"],
            job.shots,
        )
        call(
            checked_counts,
            result["counts"],
            len(job.execution_metadata["compilation"]["classical_bit_order"]),
            job.shots,
        )
        job.result = result
    job.status = status
    job.execution_metadata = {
        **job.execution_metadata,
        "provider_status": update.get("provider_status"),
        "queue": update.get("queue"),
    }
    job.polled_at = job.updated_at = now()
    if status in TERMINAL:
        job.completed_at = now()
        job.failure = (
            "Hardware provider reported job failure" if status == "FAILED" else None
        )
        audit(job)
    db.commit()


@router.get("/jobs", dependencies=[Depends(limit_requests("hardware-poll", 30))])
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [
        view(j)
        for j in db.query(HardwareJob)
        .filter_by(user_id=user.user_id)
        .order_by(HardwareJob.created_at.desc())
        .limit(20)
    ]


@router.get(
    "/jobs/{job_id}", dependencies=[Depends(limit_requests("hardware-poll", 30))]
)
def job_status(
    job_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    job = owned(db, user, job_id)
    refresh(db, job)
    return view(job)


@router.get(
    "/jobs/{job_id}/result", dependencies=[Depends(limit_requests("hardware-poll", 30))]
)
def result(
    job_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    job = owned(db, user, job_id)
    refresh(db, job)
    if job.status != "COMPLETED":
        raise HTTPException(409, "Hardware result is not available")
    return view(job)


@router.post(
    "/jobs/{job_id}/cancel",
    dependencies=[Depends(limit_requests("hardware-cancel", 5))],
)
def cancel(
    job_id: UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    job = owned(db, user, job_id)
    if job.status in TERMINAL or not job.provider_job_id:
        raise HTTPException(409, "Cancellation is not supported for this job state")
    call(provider(job.provider).cancel, job.provider_job_id)
    job.status, job.updated_at = "CANCEL_REQUESTED", now()
    db.commit()
    audit(job)
    return view(job)
