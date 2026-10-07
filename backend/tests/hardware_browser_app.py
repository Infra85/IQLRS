"""TEST-ONLY local API fixture. Never imported by app.main or enabled by deployment flags.

Run with PYTHONPATH=backend:backend/tests uvicorn hardware_browser_app:app.
Uses real auth, database, API and rate limits; only the remote QPU boundary is fake.
"""

import json
from pathlib import Path
from uuid import uuid4
from app.main import app  # noqa: F401
from app.core.config import settings
from app.core.database import SessionLocal
from app.models import User
from app.models.rate_limit import RateLimit
from app.core.security import create_access_token
from app.services.hardware import registry
from app.services.hardware.base import HardwareError
from test_hardware import FakeProvider


class BrowserProvider(FakeProvider):
    def __init__(self):
        super().__init__()
        self.jobs = {}

    def devices(self):
        good = super().devices()[0]
        return [
            good,
            {**good, "device_id": "failure-qpu", "display_name": "Failure fixture QPU"},
        ]

    def device(self, name):
        for device in self.devices():
            if device["device_id"] == name:
                return device
        raise HardwareError("Selected hardware device is unavailable")

    def submit(self, device, compiled, shots, key):
        self.submissions += 1
        remote = str(uuid4())
        self.jobs[remote] = {"device": device, "polls": 0, "canceled": False}
        return remote

    def status(self, remote):
        job = self.jobs[remote]
        job["polls"] += 1
        status = (
            "CANCELED"
            if job["canceled"]
            else "FAILED"
            if job["device"] == "failure-qpu"
            else "RUNNING"
            if job["polls"] == 1
            else "COMPLETED"
        )
        return {"status": status, "provider_status": f"TEST_{status}", "queue": None}

    def cancel(self, remote):
        self.jobs[remote]["canceled"] = True


settings.hardware_execution_enabled = True
settings.hardware_max_jobs_per_user_per_day = 20
settings.hardware_max_shots_per_user_per_day = 4096
fake = BrowserProvider()


def get_provider(name):
    if name == "ibm":
        return fake
    raise HardwareError("Braket is not configured in this test fixture")


registry.get_provider = get_provider
with SessionLocal() as db:
    tokens = []
    for label in ("a", "b"):
        user = User(
            name=f"Hardware browser {label}",
            email=f"hardware-{label}-{uuid4().hex}@example.com",
            email_verified=True,
        )
        db.add(user)
        db.flush()
        tokens.append(create_access_token({"sub": str(user.user_id)}))
    db.query(RateLimit).delete()
    db.commit()
Path("/tmp/iqlrs-hardware-browser-tokens.json").write_text(json.dumps(tokens))
Path("/tmp/iqlrs-hardware-browser-tokens.json").chmod(0o600)
