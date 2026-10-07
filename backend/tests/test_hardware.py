"""Offline provider contracts and real PostgreSQL API lifecycle. Never submits QPU jobs."""

from collections import Counter
from datetime import timedelta
from types import SimpleNamespace as NS
from unittest.mock import Mock
import pytest

from app.core.config import settings
from app.services.hardware.base import (
    Compiled,
    HardwareError,
    prepare,
    register_counts,
    checked_counts,
)
from app.services.hardware.ibm import IBMQuantumProvider
from app.services.hardware.braket import AmazonBraketProvider
from app.services.hardware import registry

CIRCUIT = {"num_qubits": 2, "shots": 16, "gates": [{"type": "X", "qubit": 0}]}


class FakeProvider:
    def __init__(self):
        self.submissions = 0
        self.current_status = "QUEUED"
        self.canceled = False

    def devices(self):
        return [
            {
                "provider": "ibm",
                "device_id": "test-qpu",
                "display_name": "Test QPU",
                "num_qubits": 5,
                "operational": True,
                "simulator": False,
                "native_gates": ["x", "h", "cx"],
                "queue": {"pending_jobs": 2},
                "capabilities": {"cancellation": True},
            }
        ]

    def device(self, name):
        if name != "test-qpu":
            raise HardwareError("Selected hardware device is unavailable")
        return self.devices()[0]

    def compile(self, device, circuit):
        self.device(device)
        _, regs, order = prepare(circuit)
        return Compiled(
            None,
            {
                "original_gate_count": len(circuit["gates"]),
                "compiled_gate_count": 3,
                "depth": 2,
                "final_qubit_count": 2,
                "routing_operations": None,
                "native_gates": ["x"],
                "transpiled": True,
                "warnings": [],
                "classical_registers": regs,
                "classical_bit_order": order,
            },
        )

    def submit(self, *args):
        self.submissions += 1
        return "provider-job-123"

    def status(self, job):
        return {
            "status": self.current_status,
            "provider_status": self.current_status,
            "queue": None,
        }

    def result(self, job, metadata, shots):
        return {"counts": {"01": shots}}

    def cancel(self, job):
        self.canceled = True


@pytest.fixture
def fake(monkeypatch):
    provider = FakeProvider()
    monkeypatch.setattr(settings, "hardware_execution_enabled", True)
    monkeypatch.setattr(registry, "get_provider", lambda _: provider)
    return provider


def test_canonical_register_order_and_correlated_shots():
    circuit = {
        **CIRCUIT,
        "classical_registers": [{"name": "a", "size": 2}, {"name": "b", "size": 1}],
        "gates": [
            {
                "type": "MEASURE_ALL",
                "destinations": [
                    {"register": "a", "bit": 0},
                    {"register": "b", "bit": 0},
                ],
            }
        ],
    }
    _, _, order = prepare(circuit)
    assert order == [{"register": "a", "bit": 0}, {"register": "b", "bit": 0}]
    assert register_counts({"a": ["01", "00"], "b": ["0", "1"]}, order, 2) == {
        "10": 1,
        "01": 1,
    }
    _, _, legacy_order = prepare(CIRCUIT)
    assert register_counts({"c": ["01"]}, legacy_order, 1) == {"01": 1}


@pytest.mark.parametrize(
    "counts,width,shots",
    [
        ({"2": 1}, 1, 1),
        ({"0": -1}, 1, 1),
        ({"00": 1}, 1, 1),
        ({"0": 1}, 1, 2),
        ({"0": True}, 1, 1),
    ],
)
def test_invalid_counts(counts, width, shots):
    with pytest.raises(HardwareError):
        checked_counts(counts, width, shots)


def test_disabled_no_sdk_initialization(monkeypatch):
    monkeypatch.setattr(settings, "hardware_execution_enabled", False)
    registry.get_provider.cache_clear()
    with pytest.raises(HardwareError, match="disabled"):
        registry.get_provider("ibm")


def test_ibm_real_sdk_translation_and_parsing():
    pytest.importorskip("qiskit_ibm_runtime")
    from qiskit.providers.fake_provider import GenericBackendV2

    backend = GenericBackendV2(3, basis_gates=["x", "sx", "rz", "cx", "id"], seed=42)
    provider = IBMQuantumProvider.__new__(IBMQuantumProvider)
    provider.service = Mock()
    provider.service.backend.return_value = backend
    provider.device = Mock(
        return_value={
            "operational": True,
            "num_qubits": 3,
            "native_gates": list(backend.target.operation_names),
        }
    )
    compiled = provider.compile("test", CIRCUIT)
    assert compiled.program.num_qubits == 3
    from qiskit_ibm_runtime.executor_sampler.prepare import prepare as sdk_prepare
    from qiskit_ibm_runtime.options_models import SamplerOptions

    program, options = sdk_prepare(
        [compiled.program],
        SamplerOptions(environment={"job_tags": ["offline-contract"]}),
        shots=16,
        backend=backend,
    )
    assert program.shots == 16
    assert options.environment.job_tags == ["offline-contract"]
    assert compiled.program.count_ops()["measure"] == 2
    assert compiled.metadata["classical_bit_order"] == [
        {"register": "c", "bit": 1},
        {"register": "c", "bit": 0},
    ]
    provider.sampler = Mock()
    provider.sampler.return_value.run.return_value.job_id.return_value = "remote"
    assert provider.submit("test", compiled, 16, "key") == "remote"
    assert provider.sampler.return_value.run.call_args.kwargs == {"shots": 16}
    data = NS(c=NS(get_bitstrings=lambda: ["01"] * 16))
    provider.service.job.return_value.result.return_value = [NS(data=data)]
    assert provider.result("remote", compiled.metadata, 16) == {"counts": {"01": 16}}
    provider.cancel("remote")
    provider.service.job.return_value.cancel.assert_called_once()


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("INITIALIZING", "VALIDATING"),
        ("DONE", "COMPLETED"),
        ("ERROR", "FAILED"),
        ("CANCELLED", "CANCELED"),
        ("new", "UNKNOWN"),
    ],
)
def test_ibm_status(raw, expected):
    provider = IBMQuantumProvider.__new__(IBMQuantumProvider)
    provider.service = Mock()
    provider.service.job.return_value.status.return_value = raw
    assert provider.status("id")["status"] == expected


def test_braket_real_sdk_translation_result_and_idempotency():
    pytest.importorskip("braket")
    provider = AmazonBraketProvider.__new__(AmazonBraketProvider)
    device = {
        "operational": True,
        "capabilities": {"gate_model": True},
        "num_qubits": 5,
        "shot_range": [1, 1000],
        "supported_operations": ["h", "cnot", "x", "measure"],
        "native_gates": ["rx", "rz"],
    }
    provider.device = Mock(return_value=device)
    compiled = provider.compile("test", CIRCUIT)
    assert "x q[0]" in compiled.program.to_ir().source
    provider._task = Mock(
        return_value=NS(
            result=lambda: NS(
                measured_qubits=[0, 1], measurement_counts=Counter({"10": 16})
            )
        )
    )
    assert provider.result("task", compiled.metadata, 16) == {"counts": {"01": 16}}
    provider.s3 = ("test-bucket", "test")
    provider._device = Mock()
    provider._device.return_value.aws_session.create_quantum_task.return_value = (
        "arn:task"
    )
    assert provider.submit("test", compiled, 16, "stable-key") == "arn:task"
    assert (
        provider._device.return_value.aws_session.create_quantum_task.call_args.kwargs[
            "clientToken"
        ]
        == "stable-key"
    )
    with pytest.raises(HardwareError, match="dynamic"):
        provider.compile("test", {**CIRCUIT, "gates": [{"type": "RESET", "qubit": 0}]})
    with pytest.raises(HardwareError, match="operation"):
        provider.compile(
            "test",
            {**CIRCUIT, "gates": [{"type": "RY", "qubit": 0, "params": {"theta": 1}}]},
        )


def body(**kw):
    return {
        "provider": "ibm",
        "device_id": "test-qpu",
        "circuit": CIRCUIT,
        "confirmed": True,
        **kw,
    }


def test_api_lifecycle_idempotency_ownership(api, fake, sessions):
    client, uid = api
    assert (
        client.get("/api/hardware/devices?provider_id=ibm").json()[0]["simulator"]
        is False
    )
    assert client.post("/api/hardware/jobs/validate", json=body()).json()["valid"]
    assert fake.submissions == 0
    assert (
        client.post(
            "/api/hardware/jobs",
            json=body(confirmed=False),
            headers={"Idempotency-Key": "test-key-1"},
        ).status_code
        == 400
    )
    response = client.post(
        "/api/hardware/jobs", json=body(), headers={"Idempotency-Key": "test-key-1"}
    )
    assert response.status_code == 202, response.text
    job = response.json()
    assert job["execution_mode"] == "HARDWARE"
    duplicate = client.post(
        "/api/hardware/jobs", json=body(), headers={"Idempotency-Key": "test-key-1"}
    )
    assert duplicate.json()["id"] == job["id"] and fake.submissions == 1
    assert (
        client.post(
            "/api/hardware/jobs",
            json=body(device_id="different"),
            headers={"Idempotency-Key": "test-key-1"},
        ).status_code
        == 409
    )
    assert client.get(f"/api/hardware/jobs/{job['id']}/result").status_code == 409
    from app.models.hardware import HardwareJob, now
    from app.models import User
    from app.core.security import create_access_token

    with sessions() as db:
        saved = db.get(HardwareJob, job["id"])
        saved.polled_at = now() - timedelta(seconds=10)
        other = User(name="Other", email="other@example.com", email_verified=True)
        db.add(other)
        db.commit()
        token = create_access_token({"sub": str(other.user_id)})
    assert (
        client.get(
            f"/api/hardware/jobs/{job['id']}",
            headers={"Authorization": f"Bearer {token}"},
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/hardware/jobs/{job['id']}/result",
            headers={"Authorization": f"Bearer {token}"},
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/hardware/jobs/{job['id']}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        ).status_code
        == 404
    )
    fake.current_status = "COMPLETED"
    result = client.get(f"/api/hardware/jobs/{job['id']}/result").json()
    assert result["result"]["counts"] == {"01": 16}
    assert "statevector" not in result["result"]
    assert client.get("/api/hardware/jobs").json()[0]["id"] == job["id"]


def test_cancel_failure_and_limits(api, fake, monkeypatch):
    client, _ = api
    monkeypatch.setattr(settings, "hardware_max_shots", 8)
    assert (
        client.post("/api/hardware/jobs/validate", json=body()).json()["valid"] is False
    )
    monkeypatch.setattr(settings, "hardware_max_shots", 1024)
    job = client.post(
        "/api/hardware/jobs", json=body(), headers={"Idempotency-Key": "cancel-key"}
    ).json()
    assert (
        client.post(f"/api/hardware/jobs/{job['id']}/cancel").json()["status"]
        == "CANCEL_REQUESTED"
    )
    assert fake.canceled
    fake.current_status = "FAILED"
    assert client.get(f"/api/hardware/jobs/{job['id']}").json()["status"] == "FAILED"
    monkeypatch.setattr(settings, "hardware_max_jobs_per_user_per_day", 1)
    assert (
        client.post(
            "/api/hardware/jobs",
            json=body(),
            headers={"Idempotency-Key": "another-key"},
        ).status_code
        == 429
    )


def test_uncertain_submission_never_retries(api, fake):
    client, _ = api
    fake.submit = Mock(side_effect=TimeoutError("token=TOPSECRET"))
    first = client.post(
        "/api/hardware/jobs", json=body(), headers={"Idempotency-Key": "uncertain-key"}
    )
    assert first.json()["status"] == "UNKNOWN"
    assert "TOPSECRET" not in first.text
    client.post(
        "/api/hardware/jobs", json=body(), headers={"Idempotency-Key": "uncertain-key"}
    )
    assert fake.submit.call_count == 1


def test_poll_rate_limit(api, fake):
    client, _ = api
    for _ in range(30):
        assert client.get("/api/hardware/jobs").status_code == 200
    assert client.get("/api/hardware/jobs").status_code == 429


def test_ibm_discovery_filters_simulators_and_dynamic_rejection():
    provider = IBMQuantumProvider.__new__(IBMQuantumProvider)
    backend = NS(
        name="dynamic-qpu",
        num_qubits=5,
        target=NS(operation_names=["x", "measure", "reset", "if_else"]),
        coupling_map=None,
        configuration=lambda: NS(simulator=False),
        status=lambda: NS(operational=True, pending_jobs=3),
    )
    simulator = NS(
        configuration=lambda: NS(simulator=True), status=lambda: NS(operational=True)
    )
    provider.service = Mock()
    provider.service.backends.return_value = [backend, simulator]
    assert len(provider.devices()) == 1
    assert provider.devices()[0]["capabilities"]["dynamic_circuits"] is True
    provider.service.backends.assert_called_with(simulator=False)
    pytest.importorskip("qiskit_ibm_runtime")
    from qiskit.providers.fake_provider import GenericBackendV2

    provider.service.backend.return_value = GenericBackendV2(
        5, basis_gates=["x", "sx", "rz", "cx"], seed=1
    )
    with pytest.raises(HardwareError, match="dynamic"):
        provider.compile(
            "dynamic-qpu",
            {
                **CIRCUIT,
                "gates": [{"type": "MEASURE", "qubit": 0}, {"type": "X", "qubit": 0}],
            },
        )


def test_braket_discovery_qpu_capabilities_queue():
    provider = AmazonBraketProvider.__new__(AmazonBraketProvider)
    action = NS(
        supportedOperations=["h", "cnot"],
        requiresAllQubitsMeasurement=True,
        requiresContiguousQubitIndices=True,
    )
    paradigm = NS(
        qubitCount=12,
        nativeGateSet=["rx", "rz"],
        connectivity=NS(dict=lambda: {"fullyConnected": True}),
    )
    properties = NS(
        action={"braket.ir.openqasm.program": action},
        paradigm=paradigm,
        service=NS(executionWindows=[], shotsRange=[1, 1000]),
    )
    device = NS(
        type="QPU",
        properties=properties,
        arn="arn:aws:braket:us-east-1::device/qpu/test/test",
        name="test",
        status="ONLINE",
        is_available=True,
        queue_depth=lambda: NS(quantum_tasks={"Normal": "4"}),
    )
    provider.session = Mock()
    provider.device_class = Mock()
    provider.device_class.get_devices.return_value = [device, NS(type="SIMULATOR")]
    devices = provider.devices()
    assert len(devices) == 1 and devices[0]["queue"] == {"Normal": "4"}
    assert devices[0]["capabilities"]["requires_all_qubits_measurement"]
    assert devices[0]["region"] == "us-east-1"
    provider.device_class.get_devices.assert_called_with(
        types=["QPU"], aws_session=provider.session
    )


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("CREATED", "VALIDATING"),
        ("QUEUED", "QUEUED"),
        ("RUNNING", "RUNNING"),
        ("COMPLETED", "COMPLETED"),
        ("FAILED", "FAILED"),
        ("CANCELLED", "CANCELED"),
        ("CANCELLING", "CANCEL_REQUESTED"),
        ("FUTURE", "UNKNOWN"),
    ],
)
def test_braket_status_cancel(raw, expected):
    provider = AmazonBraketProvider.__new__(AmazonBraketProvider)
    task = Mock()
    task.state.return_value = raw
    task.queue_position.return_value = NS(queue_position="2")
    provider._task = Mock(return_value=task)
    assert provider.status("id")["status"] == expected
    provider.cancel("id")
    task.cancel.assert_called_once()


def test_secret_error_sanitization_and_invalid_circuit(api, fake):
    client, _ = api
    bad = {**CIRCUIT, "gates": [{"type": "RX", "qubit": 0}]}
    response = client.post("/api/hardware/jobs/validate", json=body(circuit=bad))
    assert not response.json()["valid"]
    assert "finite" in response.json()["unsupported_operations"][0]
    fake.devices = Mock(side_effect=RuntimeError("AWS_SECRET_TOKEN"))
    response = client.get("/api/hardware/devices?provider_id=ibm")
    assert response.status_code == 502 and "AWS_SECRET_TOKEN" not in response.text


def test_flag_disabled_api_and_auth(api, monkeypatch):
    client, _ = api
    monkeypatch.setattr(settings, "hardware_execution_enabled", False)
    assert client.get("/api/hardware/providers").json()["enabled"] is False
    assert (
        client.post(
            "/api/hardware/jobs",
            json=body(),
            headers={"Idempotency-Key": "disabled-key"},
        ).status_code
        == 503
    )
    client.headers.pop("Authorization")
    assert client.get("/api/hardware/jobs").status_code == 401


def test_daily_shot_limit_and_submission_rate(api, fake, monkeypatch):
    client, _ = api
    monkeypatch.setattr(settings, "hardware_max_shots_per_user_per_day", 16)
    assert (
        client.post(
            "/api/hardware/jobs", json=body(), headers={"Idempotency-Key": "first-key"}
        ).status_code
        == 202
    )
    assert (
        client.post(
            "/api/hardware/jobs", json=body(), headers={"Idempotency-Key": "second-key"}
        ).status_code
        == 429
    )
    for _ in range(3):
        client.post(
            "/api/hardware/jobs", json=body(), headers={"Idempotency-Key": "first-key"}
        )
    assert (
        client.post(
            "/api/hardware/jobs", json=body(), headers={"Idempotency-Key": "first-key"}
        ).status_code
        == 429
    )
    assert fake.submissions == 1


def test_concurrent_reservations_once(api, fake):
    from concurrent.futures import ThreadPoolExecutor

    client, _ = api

    def post(_):
        return client.post(
            "/api/hardware/jobs",
            json=body(),
            headers={"Idempotency-Key": "concurrent-key"},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(post, range(2)))
    assert all(r.status_code == 202 for r in responses)
    assert responses[0].json()["id"] == responses[1].json()["id"]
    assert fake.submissions == 1


@pytest.mark.parametrize(
    "code,status,message",
    [
        ("AccessDeniedException", 503, "authentication"),
        ("ServiceQuotaExceededException", 429, "quota"),
        ("ThrottlingException", 429, "rate limit"),
        ("ValidationException", 400, "not accepted"),
        ("ConflictException", 409, "job state"),
    ],
)
def test_error_mapping_does_not_echo_secrets(code, status, message):
    from app.services.hardware.base import provider_failure

    error = RuntimeError("secret bearer credential")
    error.response = {"Error": {"Code": code, "Message": "secret bearer credential"}}
    actual, safe, definite = provider_failure(error)
    assert actual == status and message in safe and definite
    assert "secret" not in safe


def test_measurement_conditions_rejected():
    with pytest.raises(HardwareError, match="unwritten-bit"):
        prepare(
            {
                **CIRCUIT,
                "classical_registers": [{"name": "c", "size": 2}],
                "gates": [
                    {
                        "type": "MEASURE",
                        "qubit": 0,
                        "destinations": [{"register": "c", "bit": 0}],
                        "condition": {
                            "register": "c",
                            "bit": 1,
                            "operator": "eq",
                            "value": 1,
                        },
                    }
                ],
            }
        )


def test_migration_creates_owned_table_and_downgrades(sessions):
    from pathlib import Path
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect
    from app.models.hardware import HardwareJob

    with sessions().get_bind().begin() as connection:
        HardwareJob.__table__.drop(connection)
        config = Config()
        config.set_main_option(
            "script_location", str(Path(__file__).resolve().parents[1] / "migrations")
        )
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        inspector = inspect(connection)
        assert inspector.has_table("hardware_jobs")
        assert (
            inspector.get_foreign_keys("hardware_jobs")[0]["referred_table"] == "users"
        )
        assert set(
            inspector.get_unique_constraints("hardware_jobs")[0]["column_names"]
        ) == {"user_id", "idempotency_key"}
        command.upgrade(config, "head")
        command.downgrade(config, "base")
        assert not inspect(connection).has_table("hardware_jobs")


def test_optional_provider_initialization_authentication(monkeypatch):
    pytest.importorskip("qiskit_ibm_runtime")
    import qiskit_ibm_runtime
    import qiskit_ibm_runtime.executor_sampler

    boto3 = pytest.importorskip("boto3")
    pytest.importorskip("braket.aws")
    import braket.aws

    service = Mock()
    monkeypatch.setattr(qiskit_ibm_runtime, "QiskitRuntimeService", service)
    config = NS(
        ibm_quantum_token="test-credential",
        ibm_quantum_instance="test-instance",
        braket_region="us-east-1",
        braket_s3_bucket="test-bucket",
        braket_s3_prefix="test",
    )
    IBMQuantumProvider(config)
    service.assert_called_once_with(
        channel="ibm_quantum_platform",
        token="test-credential",
        instance="test-instance",
    )
    session = Mock()
    monkeypatch.setattr(boto3, "Session", Mock(return_value=session))
    monkeypatch.setattr(braket.aws, "AwsSession", Mock())
    AmazonBraketProvider(config)
    session.client.return_value.get_caller_identity.assert_called_once()
    session.get_credentials.return_value = None
    with pytest.raises(HardwareError, match="credentials"):
        AmazonBraketProvider(config)


def test_local_endpoint_never_accepts_hardware_mode(api):
    client, _ = api
    response = client.post(
        "/api/circuits/simulate", json={**CIRCUIT, "execution_mode": "HARDWARE"}
    )
    assert response.status_code == 422
    response = client.post("/api/circuits/simulate", json=CIRCUIT)
    assert response.status_code == 200
    assert response.json()["execution_mode"] == "LOCAL_SIMULATION"


def test_ibm_dynamic_circuit_preserves_registers_and_conditions():
    pytest.importorskip("qiskit_ibm_runtime")
    from qiskit.providers.fake_provider import GenericBackendV2

    backend = GenericBackendV2(
        3, basis_gates=["x", "sx", "rz", "cx"], control_flow=True, seed=2
    )
    adapter = IBMQuantumProvider.__new__(IBMQuantumProvider)
    adapter.service = Mock()
    adapter.service.backend.return_value = backend
    adapter.device = Mock(
        return_value={
            "operational": True,
            "num_qubits": 3,
            "native_gates": list(backend.target.operation_names),
        }
    )
    data = {
        **CIRCUIT,
        "classical_registers": [{"name": "readout", "size": 2}],
        "gates": [
            {"type": "H", "qubit": 0},
            {
                "type": "MEASURE",
                "qubit": 0,
                "destinations": [{"register": "readout", "bit": 0}],
            },
            {
                "type": "X",
                "qubit": 1,
                "condition": {
                    "register": "readout",
                    "bit": 0,
                    "operator": "eq",
                    "value": 1,
                },
            },
            {"type": "RESET", "qubit": 0},
            {
                "type": "MEASURE",
                "qubit": 1,
                "destinations": [{"register": "readout", "bit": 1}],
            },
        ],
    }
    compiled = adapter.compile("test", data)
    assert compiled.program.count_ops()["if_else"] == 1
    assert compiled.program.count_ops()["reset"] == 1
    assert compiled.program.cregs[0].name == "readout"
    assert compiled.metadata["classical_bit_order"] == [
        {"register": "readout", "bit": 1},
        {"register": "readout", "bit": 0},
    ]
