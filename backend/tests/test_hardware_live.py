"""Opt-in paid QPU smoke tests. Ordinary CI always skips these tests."""

import os
import time
from uuid import uuid4
import pytest

from app.core.config import settings
from app.services.hardware.registry import get_provider
from app.services.hardware.base import checked_counts

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_HARDWARE_INTEGRATION_TESTS") != "true",
    reason="Real QPU tests require explicit opt-in",
)


@pytest.mark.parametrize("name", ["ibm", "braket"])
def test_live_qpu(name):
    device_id = os.getenv(f"HARDWARE_TEST_{name.upper()}_DEVICE")
    if not device_id:
        pytest.skip(f"No explicitly configured {name} test device")
    assert settings.hardware_execution_enabled, (
        "HARDWARE_EXECUTION_ENABLED must be true"
    )
    shots = int(os.getenv("HARDWARE_TEST_SHOTS", "16"))
    assert 1 <= shots <= min(32, settings.hardware_max_shots)
    adapter = get_provider(name)
    device = adapter.device(device_id)
    assert device["operational"] and not device["simulator"]
    circuit = {
        "num_qubits": 2,
        "shots": shots,
        "gates": [
            {"type": "H", "qubit": 0},
            {"type": "CNOT", "control": 0, "target": 1},
        ],
    }
    compiled = adapter.compile(device_id, circuit)
    remote_id = adapter.submit(device_id, compiled, shots, str(uuid4()))
    assert remote_id
    # Print only provider/job identifiers for operator recovery if the bounded wait expires.
    print(
        {
            "provider": name,
            "device": device_id,
            "provider_job_id": remote_id,
            "shots": shots,
        }
    )
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        status = adapter.status(remote_id)
        if status["status"] == "COMPLETED":
            result = adapter.result(remote_id, compiled.metadata, shots)
            checked_counts(result["counts"], 2, shots)
            # Loose sanity check, never require ideal/exact Bell counts from a noisy QPU.
            assert (
                result["counts"].get("00", 0) + result["counts"].get("11", 0)
                >= shots * 0.25
            )
            assert "statevector" not in result
            assert not any(
                word in result for word in ("token", "credentials", "secret")
            )
            return
        assert status["status"] not in {"FAILED", "CANCELED"}, status
        time.sleep(5)
    pytest.fail(
        f"Live QPU wait exceeded 300s. Job remains tracked at provider: {remote_id}; do not resubmit automatically"
    )
