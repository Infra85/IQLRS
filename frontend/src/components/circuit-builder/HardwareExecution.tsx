"use client";

import { useEffect, useState } from "react";
import { apiFetch, simulateCircuit, type CircuitRequest } from "@/lib/api";
import { Button } from "@/components/ui/button";

type Device = { device_id: string; display_name: string; num_qubits: number; operational: boolean; native_gates: string[]; queue: Record<string, unknown> | null; capabilities: Record<string, unknown> };
type Compilation = { original_gate_count: number; compiled_gate_count: number; depth: number; final_qubit_count: number; routing_operations: number | null; native_gates: string[]; transpiled: boolean; warnings: string[]; classical_bit_order: { register: string; bit: number }[] };
type Validation = { valid: boolean; unsupported_operations: string[]; compilation: Compilation | null; warnings: string[] };
type Job = { id: string; provider: string; device_id: string; provider_job_id: string | null; status: string; shots: number; failure: string | null; circuit: CircuitRequest; result: { counts: Record<string, number> } | null; metadata: { queue?: Record<string, unknown>; compilation: Compilation } };
const terminal = new Set(["COMPLETED", "FAILED", "CANCELED"]);

export function HardwareExecution({ circuit, mode, onMode }: { circuit: CircuitRequest; mode: string; onMode: (mode: string) => void }) {
  const [config, setConfig] = useState<{ enabled: boolean; max_shots: number; providers: { id: string; available: boolean; reason: string | null }[] } | null>(null);
  const [devices, setDevices] = useState<Device[]>([]);
  const [deviceId, setDeviceId] = useState("");
  const [validation, setValidation] = useState<Validation | null>(null);
  const [validatedInput, setValidatedInput] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [job, setJob] = useState<Job | null>(null);
  const [history, setHistory] = useState<Job[]>([]);
  const [comparison, setComparison] = useState<Record<string, number> | null>(null);
  const [comparisonShots, setComparisonShots] = useState(0);
  const [retry, setRetry] = useState<{ key: string; input: string } | null>(null);
  const input = JSON.stringify({ provider: mode, device_id: deviceId, circuit });
  const valid = validation?.valid && validatedInput === input;
  const device = devices.find(d => d.device_id === deviceId);

  useEffect(() => {
    apiFetch("/api/hardware/providers").then(setConfig).catch(() => setConfig(null));
  }, []);
  useEffect(() => {
    if (!config?.enabled || !localStorage.getItem("access_token")) return;
    apiFetch("/api/hardware/jobs").then((jobs: Job[]) => { setHistory(jobs); setJob(jobs[0] ?? null); }).catch(e => setError(e.message));
  }, [config]);
  useEffect(() => {
    setDevices([]); setDeviceId(""); setValidation(null); setConfirm(false);
    if (mode === "local") return;
    let active = true;
    apiFetch(`/api/hardware/devices?provider_id=${encodeURIComponent(mode)}&operational_only=false`).then((items: Device[]) => {
      if (active) { setDevices(items); setDeviceId(items.find(d => d.operational)?.device_id ?? ""); }
    }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [mode]);
  useEffect(() => {
    if (!job || terminal.has(job.status) || !job.provider_job_id) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    let delay = 5000;
    const poll = async () => {
      try {
        const next: Job = await apiFetch(`/api/hardware/jobs/${job.id}`);
        if (!active) return;
        setJob(next);
        if (terminal.has(next.status)) return;
      } catch (e) { if (active) setError((e as Error).message); }
      delay = Math.min(30000, delay * 1.5);
      if (active) timer = setTimeout(poll, delay);
    };
    timer = setTimeout(poll, delay);
    return () => { active = false; clearTimeout(timer); };
  }, [job?.id, job?.provider_job_id, job?.status]); // eslint-disable-line react-hooks/exhaustive-deps

  async function action(fn: () => Promise<void>) {
    setBusy(true); setError("");
    try { await fn(); } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  if (!config?.enabled) return null;
  return <section className="panel p-5 space-y-4 min-w-0 break-words" aria-label="Hardware execution">
    <label>Execution Target <select aria-label="Execution Target" value={mode} disabled={busy} onChange={e => { onMode(e.target.value); setError(""); }} className="bg-surface-raised p-2 rounded">
      <option value="local">Local Simulator</option>
      {config.providers.filter(p => p.available).map(p => <option key={p.id} value={p.id}>{p.id === "ibm" ? "IBM Quantum" : "Amazon Braket"}</option>)}
    </select></label>
    {config.providers.filter(p => !p.available).map(p => <p key={p.id}>{p.id}: {p.reason}</p>)}
    {mode !== "local" && <>
      <p className="font-bold text-amber-300">REAL QUANTUM HARDWARE</p>
      <p>Hardware jobs may consume provider quota or incur charges. Sign in to submit. Maximum {config.max_shots} shots per job.</p>
      <label>Device <select aria-label="Hardware device" className="bg-surface-raised p-2 rounded max-w-full" value={deviceId} disabled={busy} onChange={e => { setDeviceId(e.target.value); setConfirm(false); }}>
        <option value="">Select a QPU</option>
        {devices.map(d => <option key={d.device_id} value={d.device_id} disabled={!d.operational}>{d.display_name} · {d.num_qubits} qubits · {d.operational ? "Available" : "Unavailable"}</option>)}
      </select></label>
      {device && <div><p>{device.num_qubits} device qubits · {circuit.num_qubits} circuit qubits · {circuit.shots} shots</p>
        <p>Queue: {device.queue ? JSON.stringify(device.queue) : "Queue information unavailable"}</p>
        <p>Native gates: {device.native_gates.join(", ")}</p>
        <p>Capabilities: {JSON.stringify(device.capabilities)}</p></div>}
      <p>Hardware provides measured counts, not exact statevectors or internal debug checkpoints.</p>
      <Button disabled={busy || !deviceId} onClick={() => action(async () => {
        const data = await apiFetch("/api/hardware/jobs/validate", { method: "POST", body: input });
        setValidation(data); setValidatedInput(input); setConfirm(false);
      })}>Validate for hardware</Button>
      {validation && validatedInput === input && <div role="status">
        <p>Hardware validation {validation.valid ? "PASSED" : "FAILED"}</p>
        {validation.unsupported_operations.map(s => <p key={s}>{s}</p>)}
        {validation.compilation && <p>Original: {validation.compilation.original_gate_count} gates. Compiled: {validation.compilation.compiled_gate_count} instructions; depth {validation.compilation.depth}; {validation.compilation.final_qubit_count} qubits. Routing: {validation.compilation.routing_operations ?? "unavailable"}.</p>}
        {validation.warnings.map(s => <p key={s}>{s}</p>)}
      </div>}
      <Button disabled={busy || !valid} onClick={() => setConfirm(true)}>Review QPU submission</Button>
      {confirm && valid && <div role="dialog" aria-label="Confirm real QPU execution" className="border border-amber-400 p-4 space-y-3">
        <h3>REAL QUANTUM HARDWARE</h3>
        <p>Provider: {mode === "ibm" ? "IBM Quantum" : "Amazon Braket"} · Device: {device?.display_name}</p>
        <p>{circuit.num_qubits} circuit qubits · Shots: {circuit.shots}</p>
        <p>Queue: {device?.queue ? JSON.stringify(device.queue) : "Queue information unavailable"}</p>
        <p>This will submit a real quantum job and may incur charges. {validation?.compilation?.transpiled ? "The circuit is transpiled for this target." : "The provider will compile and route the circuit."} Unsupported operations block submission.</p>
        <Button variant="secondary" disabled={busy} onClick={() => setConfirm(false)}>Cancel</Button>
        <Button disabled={busy} onClick={() => action(async () => {
          const key = retry?.input === input ? retry.key : crypto.randomUUID();
          setRetry({ key, input });
          const next: Job = await apiFetch("/api/hardware/jobs", { method: "POST", headers: { "Idempotency-Key": key }, body: JSON.stringify({ ...JSON.parse(input), confirmed: true }) });
          setJob(next); setHistory(h => [next, ...h.filter(j => j.id !== next.id)]); setComparison(null); setConfirm(false);
        })}>{busy ? "Submitting…" : "Submit to QPU"}</Button>
      </div>}
    </>}
    {error && <p role="alert">{error}</p>}
    {history.length > 0 && <label>Saved hardware jobs <select aria-label="Saved hardware jobs" className="bg-surface-raised p-2 rounded max-w-full" value={job?.id ?? ""} onChange={e => { setJob(history.find(j => j.id === e.target.value) ?? null); setComparison(null); }}>
      {history.map(j => <option key={j.id} value={j.id}>{j.provider} · {j.id}</option>)}
    </select></label>}
    {job && <section aria-label="Hardware job" className="space-y-3">
      <h3 className="font-bold">Hardware Job · {job.status}</h3>
      <p className="break-all">Provider: {job.provider} · Device: {job.device_id}</p>
      <p className="break-all">IQLRS job ID: {job.id} · Provider job ID: {job.provider_job_id ?? "Not yet recorded"}</p>
      <p>Shots: {job.shots} · Queue: {job.metadata.queue ? JSON.stringify(job.metadata.queue) : "Queue information unavailable"}</p>
      {job.failure && <p role="alert">{job.failure}</p>}
      {!terminal.has(job.status) && job.provider_job_id && <Button disabled={busy || job.status === "CANCEL_REQUESTED"} onClick={() => action(async () => setJob(await apiFetch(`/api/hardware/jobs/${job.id}/cancel`, { method: "POST" })))}>Cancel job</Button>}
      {job.result && <>
        <h3 className="font-bold text-amber-300">REAL HARDWARE RESULT</h3>
        <p>Results may differ from ideal simulation because physical quantum hardware is noisy. Gate errors, routing, calibration and readout effects can change the distribution.</p>
        <p>Bit order: {job.metadata.compilation.classical_bit_order.map(d => `${d.register}[${d.bit}]`).join(" ")}</p>
        <Button disabled={busy} onClick={() => action(async () => {
          const local = await simulateCircuit({ ...job.circuit, execution_mode: "LOCAL_SIMULATION", debug: undefined, shots: Math.min(job.shots, 256) });
          setComparison(local.counts); setComparisonShots(Math.min(job.shots, 256));
        })}>Compare with local simulation</Button>
        <table className="w-full text-left"><thead><tr><th>Bits</th><th>Hardware counts</th><th>Hardware</th>{comparison && <th>Local simulation</th>}</tr></thead><tbody>
          {Array.from(new Set([...Object.keys(job.result.counts), ...Object.keys(comparison ?? {})])).sort().map(bits => <tr key={bits}><td>{bits}</td><td>{job.result!.counts[bits] ?? 0}</td><td>{((job.result!.counts[bits] ?? 0) / job.shots * 100).toFixed(1)}%</td>{comparison && <td>{((comparison[bits] ?? 0) / comparisonShots * 100).toFixed(1)}%</td>}</tr>)}
        </tbody></table>
      </>}
    </section>}
  </section>;
}
