"""Amazon Braket QPU adapter. Only discovered gate-model QPUs are executable."""

from collections import Counter
from app.services.hardware.base import (
    Compiled,
    HardwareError,
    HardwareProvider,
    prepare,
    checked_counts,
)


class AmazonBraketProvider(HardwareProvider):
    def __init__(self, settings):
        import boto3
        from botocore.config import Config
        from braket.aws import AwsDevice, AwsSession, AwsQuantumTask

        session = boto3.Session(region_name=settings.braket_region)
        if session.get_credentials() is None:
            raise HardwareError("AWS credentials not configured")
        config = Config(connect_timeout=5, read_timeout=15, retries={"max_attempts": 0})
        # Resolve and authenticate the standard AWS chain before advertising availability.
        session.client("sts", config=config).get_caller_identity()
        self.session = AwsSession(boto_session=session, config=config)
        self.device_class, self.task_class = AwsDevice, AwsQuantumTask
        self.s3 = (settings.braket_s3_bucket, settings.braket_s3_prefix)

    def _device(self, device_id):
        # Never instantiate an arbitrary client-supplied URL/ARN before discovery.
        self.device(device_id)
        return self.device_class(device_id, aws_session=self.session)

    def devices(self):
        result = []
        for d in self.device_class.get_devices(types=["QPU"], aws_session=self.session):
            if str(d.type) not in {"QPU", "AwsDeviceType.QPU"}:
                continue
            props = d.properties
            action = props.action.get("braket.ir.openqasm.program")
            paradigm = getattr(props, "paradigm", None)
            queue = None
            try:
                queue = {
                    str(k): str(v) for k, v in d.queue_depth().quantum_tasks.items()
                }
            except Exception:
                pass  # Optional queue permission is not required for execution.
            connectivity = getattr(paradigm, "connectivity", None)
            result.append(
                {
                    "provider": "braket",
                    "device_id": d.arn,
                    "display_name": d.name,
                    "num_qubits": getattr(paradigm, "qubitCount", 0),
                    "simulator": False,
                    "operational": d.status == "ONLINE" and d.is_available,
                    "native_gates": list(getattr(paradigm, "nativeGateSet", [])),
                    "supported_operations": list(
                        getattr(action, "supportedOperations", [])
                    ),
                    "topology": connectivity.dict() if connectivity else None,
                    "queue": queue,
                    "region": d.arn.split(":")[3],
                    "availability": [w.dict() for w in props.service.executionWindows],
                    "shot_range": list(props.service.shotsRange),
                    "capabilities": {
                        "gate_model": action is not None and paradigm is not None,
                        "dynamic_circuits": False,
                        "reset": False,
                        "cancellation": True,
                        "requires_all_qubits_measurement": bool(
                            getattr(action, "requiresAllQubitsMeasurement", False)
                        ),
                        "requires_contiguous_qubits": bool(
                            getattr(action, "requiresContiguousQubitIndices", False)
                        ),
                    },
                }
            )
        return result

    def compile(self, device_id, circuit):
        from braket.circuits import Circuit

        device = self.device(device_id)
        if not device["operational"]:
            raise HardwareError(
                "Selected device is offline or outside its availability window"
            )
        if not device["capabilities"]["gate_model"]:
            raise HardwareError(
                "Selected QPU does not expose a supported gate-model action"
            )
        if circuit["num_qubits"] > device["num_qubits"]:
            raise HardwareError("Circuit exceeds device qubit count")
        if not device["shot_range"][0] <= circuit["shots"] <= device["shot_range"][1]:
            raise HardwareError("Shots are outside the device's supported range")
        ops, regs, order = prepare(circuit)
        qc = Circuit()
        measured = False
        mapping = {}
        supported = {s.lower() for s in device["supported_operations"]}
        for op in ops:
            if op["condition"] or op["type"] == "RESET":
                raise HardwareError(
                    "This Braket adapter does not support dynamic conditions or reset"
                )
            if op["destinations"]:
                measured = True
                for q, d in zip(op["targets"], op["destinations"]):
                    mapping[(d["register"], d["bit"])] = q
                continue
            if measured:
                raise HardwareError(
                    "This Braket adapter does not support mid-circuit measurement"
                )
            name = op["type"].lower()
            if op["controls"]:
                name = {"X": "cnot", "Y": "cy", "Z": "cz"}.get(
                    op["base"], "unsupported"
                )
                if len(op["controls"]) != 1:
                    raise HardwareError(
                        "Braket multi-controlled operations are not supported by this adapter"
                    )
            if name not in supported or not hasattr(qc, name):
                raise HardwareError(
                    f"Selected device does not support operation {op['type']}"
                )
            getattr(qc, name)(*(op["controls"] + op["targets"]), *op["params"].values())
        qubits = sorted(set(mapping.values()))
        # Braket measure explicitly includes idle qubits and defines result columns.
        used = set(int(q) for q in qc.qubits) | set(qubits)
        if device["capabilities"].get(
            "requires_all_qubits_measurement"
        ) and used != set(qubits):
            raise HardwareError(
                "Selected device requires measurement of every used qubit"
            )
        if device["capabilities"].get("requires_contiguous_qubits") and used != set(
            range(max(used) + 1)
        ):
            raise HardwareError("Selected device requires contiguous qubit indices")
        qc.measure(qubits)
        metadata = {
            "original_gate_count": len(circuit["gates"]),
            "compiled_gate_count": len(qc.instructions),
            "depth": qc.depth,
            "original_depth": None,
            "final_qubit_count": qc.qubit_count,
            "routing_operations": None,
            "native_gates": device["native_gates"],
            "classical_registers": regs,
            "classical_bit_order": order,
            "measurement_qubits": [mapping[(d["register"], d["bit"])] for d in order],
            "transpiled": False,
            "warnings": [
                "Provider compiles OpenQASM and routes virtual qubits; final physical depth and routing are unavailable before submission."
            ],
        }
        return Compiled(qc, metadata)

    def submit(self, device_id, compiled, shots, key):
        from braket.circuits.serialization import IRType

        device = self._device(device_id)
        # AwsDevice.run forwards unknown kwargs to the task constructor, not CreateQuantumTask.
        # Use the SDK service method so the stable clientToken reaches AWS.
        return device.aws_session.create_quantum_task(
            deviceArn=device_id,
            action=compiled.program.to_ir(ir_type=IRType.OPENQASM).json(),
            outputS3Bucket=self.s3[0],
            outputS3KeyPrefix=self.s3[1],
            shots=shots,
            clientToken=key,
        )

    def _task(self, job_id):
        return self.task_class(
            job_id,
            aws_session=self.session.copy_session(region=job_id.split(":")[3]),
            poll_timeout_seconds=10,
        )

    def status(self, job_id):
        task = self._task(job_id)
        raw = task.state()
        queue = None
        if raw == "QUEUED":
            try:
                queue = {"position": str(task.queue_position().queue_position)}
            except Exception:
                pass
        return {
            "status": {
                "CREATED": "VALIDATING",
                "QUEUED": "QUEUED",
                "RUNNING": "RUNNING",
                "COMPLETED": "COMPLETED",
                "FAILED": "FAILED",
                "CANCELLED": "CANCELED",
                "CANCELLING": "CANCEL_REQUESTED",
            }.get(raw, "UNKNOWN"),
            "provider_status": raw,
            "queue": queue,
        }

    def result(self, job_id, metadata, shots):
        result = self._task(job_id).result()
        if result is None:
            raise HardwareError("Job result unavailable")
        qubits = list(result.measured_qubits)
        counts = Counter()
        checked_counts(dict(result.measurement_counts), len(qubits), shots)
        for bits, count in result.measurement_counts.items():
            try:
                key = "".join(
                    bits[qubits.index(q)] for q in metadata["measurement_qubits"]
                )
            except (ValueError, IndexError):
                raise HardwareError(
                    "Provider measurement qubits are incomplete"
                ) from None
            counts[key] += int(count)
        return {
            "counts": checked_counts(
                dict(counts), len(metadata["classical_bit_order"]), shots
            )
        }

    def cancel(self, job_id):
        self._task(job_id).cancel()
