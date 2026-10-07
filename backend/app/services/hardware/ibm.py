"""IBM Quantum Compute client-side Sampler adapter (runtime >= 0.50)."""

from app.services.hardware.base import (
    Compiled,
    HardwareError,
    HardwareProvider,
    prepare,
    register_counts,
)


class IBMQuantumProvider(HardwareProvider):
    def __init__(self, settings):
        from qiskit_ibm_runtime import QiskitRuntimeService
        from qiskit_ibm_runtime.executor_sampler import Sampler

        self.sampler = Sampler
        self.service = QiskitRuntimeService(
            channel="ibm_quantum_platform",
            token=settings.ibm_quantum_token,
            instance=settings.ibm_quantum_instance,
        )

    def devices(self):
        result = []
        for backend in self.service.backends(simulator=False):
            status = backend.status()
            config = backend.configuration()
            if config.simulator:
                continue
            result.append(
                {
                    "provider": "ibm",
                    "device_id": backend.name,
                    "display_name": backend.name,
                    "num_qubits": backend.num_qubits,
                    "operational": bool(status.operational),
                    "simulator": False,
                    "max_shots": getattr(config, "max_shots", None),
                    "native_gates": sorted(backend.target.operation_names),
                    "topology": list(backend.coupling_map.get_edges())
                    if backend.coupling_map
                    else None,
                    "queue": {"pending_jobs": status.pending_jobs},
                    "region": None,
                    "availability": None,
                    "capabilities": {
                        "dynamic_circuits": "if_else" in backend.target.operation_names,
                        "reset": "reset" in backend.target.operation_names,
                        "cancellation": True,
                    },
                }
            )
        return result

    def compile(self, device_id, circuit):
        from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
        from qiskit.circuit.library import (
            HGate,
            XGate,
            YGate,
            ZGate,
            IGate,
            SGate,
            TGate,
            RXGate,
            RYGate,
            RZGate,
        )

        device = self.device(device_id)
        if not device["operational"]:
            raise HardwareError("Selected device is offline or not accepting jobs")
        if circuit["num_qubits"] > device["num_qubits"]:
            raise HardwareError("Circuit exceeds device qubit count")
        if device.get("max_shots") and circuit["shots"] > device["max_shots"]:
            raise HardwareError("Shots exceed the selected backend limit")
        ops, regs, order = prepare(circuit)
        backend = self.service.backend(device_id)
        names = set(backend.target.operation_names)
        seen_measurement = False
        for op in ops:
            dynamic = op["condition"] is not None or (
                seen_measurement and not op["destinations"]
            )
            if dynamic and "if_else" not in names:
                raise HardwareError(
                    "Selected backend does not support requested dynamic circuit features"
                )
            if op["type"] == "RESET" and "reset" not in names:
                raise HardwareError("Selected backend does not support reset")
            seen_measurement |= bool(op["destinations"])
        cregs = {r["name"]: ClassicalRegister(r["size"], r["name"]) for r in regs}
        qc = QuantumCircuit(
            QuantumRegister(circuit["num_qubits"], "__iqlrs_q"), *cregs.values()
        )
        constructors = dict(
            H=HGate,
            X=XGate,
            Y=YGate,
            Z=ZGate,
            I=IGate,
            S=SGate,
            T=TGate,
            RX=RXGate,
            RY=RYGate,
            RZ=RZGate,
        )

        def append(op):
            if op["destinations"]:
                for q, d in zip(op["targets"], op["destinations"]):
                    qc.measure(q, cregs[d["register"]][d["bit"]])
            elif op["type"] == "RESET":
                qc.reset(op["targets"][0])
            elif op["type"] == "SWAP":
                qc.swap(*op["targets"])
            else:
                gate = constructors[op["base"]](*op["params"].values())
                if op["controls"]:
                    gate = gate.control(len(op["controls"]))
                qc.append(gate, op["controls"] + op["targets"])

        for op in ops:
            condition = op["condition"]
            if condition:
                register = cregs[condition["register"]]
                target = (
                    register if condition["bit"] is None else register[condition["bit"]]
                )
                with qc.if_test((target, condition["value"])):
                    append(op)
            else:
                append(op)
        compiled = transpile(
            qc, backend=backend, optimization_level=1, seed_transpiler=42
        )
        metadata = {
            "original_gate_count": len(circuit["gates"]),
            "original_depth": qc.depth(),
            "compiled_gate_count": compiled.size(),
            "depth": compiled.depth(),
            "final_qubit_count": compiled.num_qubits,
            "routing_operations": None,
            "native_gates": device["native_gates"],
            "classical_registers": regs,
            "classical_bit_order": order,
            "transpiled": True,
            "warnings": [
                "Routing operation count is not separately reported; gate count changes include decomposition."
            ],
        }
        return Compiled(compiled, metadata)

    def submit(self, device_id, compiled, shots, key):
        sampler = self.sampler(
            mode=self.service.backend(device_id),
            options={"environment": {"job_tags": [key]}},
        )
        return sampler.run([compiled.program], shots=shots).job_id()

    def status(self, job_id):
        raw = self.service.job(job_id).status()
        return {
            "status": {
                "INITIALIZING": "VALIDATING",
                "QUEUED": "QUEUED",
                "RUNNING": "RUNNING",
                "DONE": "COMPLETED",
                "ERROR": "FAILED",
                "CANCELLED": "CANCELED",
            }.get(raw, "UNKNOWN"),
            "provider_status": raw,
            "queue": None,
        }

    def result(self, job_id, metadata, shots):
        pub = self.service.job(job_id).result(timeout=10)[0]
        samples = {
            r["name"]: getattr(pub.data, r["name"]).get_bitstrings()
            for r in metadata["classical_registers"]
        }
        if any(
            len(bits) != r["size"] or set(bits) - {"0", "1"}
            for r in metadata["classical_registers"]
            for bits in samples[r["name"]]
        ):
            raise HardwareError("Provider returned invalid measurement register widths")
        if any(len(s) != shots for s in samples.values()):
            raise HardwareError("Provider returned incomplete register samples")
        return {
            "counts": register_counts(samples, metadata["classical_bit_order"], shots)
        }

    def cancel(self, job_id):
        self.service.job(job_id).cancel()
