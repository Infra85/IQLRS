"use client";
import { useEffect, useState } from "react";
import { Select } from "@/components/ui/input";
import { checkpointStatus, operationLabel, stepCheckpoint, type DebugResult } from "@/lib/simulation-trace";
import { QuantumStateTable } from "./QuantumStateTable";

export function ExecutionTrace({ debug, onOperation }: { debug: DebugResult; onOperation: (index: number | null) => void }) {
  const [shotIndex, setShotIndex] = useState(0);
  const [checkpointIndex, setCheckpointIndex] = useState(0);
  const trace = debug.traces[shotIndex] ?? debug.traces[0];
  const current = Math.min(checkpointIndex, trace.checkpoints.length - 1);
  const checkpoint = trace.checkpoints[current];
  const operation = checkpoint.operation_index === null ? null : debug.operations[String(checkpoint.operation_index)];
  useEffect(() => { setShotIndex(0); setCheckpointIndex(0); }, [debug]);
  useEffect(() => { onOperation(checkpoint.operation_index); }, [checkpoint, onOperation]);
  return <section className="panel p-5 lg:col-span-2 min-w-0 space-y-5" aria-label="Execution trace">
    <h2 className="section-title">Debug execution</h2>
    <p className="text-sm text-slate-400">Quantum and classical state belong to the selected shot immediately after the checkpointed operation. These are not aggregate results. Start shows initialization; end preserves the circuit state before any implicit terminal readout.</p>
    <div className="flex flex-wrap gap-3 items-end">
      <label className="text-sm">Shot
        <Select aria-label="Debug shot" value={trace.shot} onChange={e => { setShotIndex(debug.traces.findIndex(s => s.shot === Number(e.target.value))); setCheckpointIndex(0); }}>
          {debug.traces.map(s => <option key={s.shot} value={s.shot}>Shot {s.shot}</option>)}
        </Select>
      </label>
      <button type="button" className="ui-button button-secondary" disabled={current === 0} onClick={() => setCheckpointIndex(stepCheckpoint(current, -1, trace.checkpoints.length))}>Previous checkpoint</button>
      <button type="button" className="ui-button button-secondary" disabled={current === trace.checkpoints.length - 1} onClick={() => setCheckpointIndex(stepCheckpoint(current, 1, trace.checkpoints.length))}>Next checkpoint</button>
      <p role="status" className="text-sm">Shot {trace.shot} · checkpoint {current + 1} of {trace.checkpoints.length}</p>
    </div>
    <div className="grid gap-5 lg:grid-cols-2">
      <ol aria-label="Execution timeline" className="max-h-96 overflow-auto space-y-2">
        {trace.checkpoints.map((cp, index) => <li key={index}>
          <button type="button" aria-current={index === current ? "step" : undefined} onClick={() => setCheckpointIndex(index)}
            className={`w-full rounded border p-3 text-left text-sm ${index === current ? "border-quantum-300 bg-quantum-950" : "border-white/10"}`}>
            {cp.operation_index === null ? cp.kind === "start" ? "Simulation start" : "Simulation end" : `Operation ${cp.operation_index + 1}: ${operationLabel(debug.operations[String(cp.operation_index)])}`}
            <span className="block mt-1 text-xs">{cp.condition && `Condition ${cp.condition.matched ? "TRUE" : "FALSE"} · `}{checkpointStatus(cp)}</span>
          </button>
        </li>)}
      </ol>
      <div className="space-y-4 min-w-0" aria-label="Checkpoint details" role="region">
        <h3 className="font-semibold">{operation ? operationLabel(operation) : checkpoint.kind === "start" ? "Initial state" : "Final circuit state"}</h3>
        <p className="text-sm">Execution: {checkpointStatus(checkpoint)}</p>
        {operation && <p className="text-sm">Quantum controls: {operation.controls.length ? operation.controls.map(q => `q${q}`).join(", ") : "none"}</p>}
        {checkpoint.condition && <div className="rounded border border-dashed border-white/30 p-3 text-sm" role="region" aria-label="Classical condition evaluation">
          <h4 className="font-semibold">Classical condition</h4>
          <p>Actual: {checkpoint.condition.actual} · Expected: {checkpoint.condition.expected}</p>
          <p>Evaluation: {checkpoint.condition.matched ? "TRUE" : "FALSE"} · {checkpoint.executed ? "EXECUTED" : "SKIPPED"}</p>
        </div>}
        <div className="text-sm" role="region" aria-label="Checkpoint classical state">
          <h4 className="font-semibold">Classical state · shot {trace.shot}</h4>
          {Object.entries(checkpoint.classical).map(([name, bits]) => <p key={name} className="font-mono">{name} = {bits}</p>)}
        </div>
        {!!checkpoint.samples.length && <div className="text-sm space-y-3" role="region" aria-label={checkpoint.kind === "reset" ? "Reset event" : "Measurement event"}>
          <h4 className="font-semibold">{checkpoint.kind === "reset" ? "Reset event" : "Measurement event"}</h4>
          {checkpoint.samples.map(sample => <div key={sample.qubit} className="rounded border border-white/10 p-3">
            <p>q{sample.qubit}{sample.destination ? ` → ${sample.destination.register}[${sample.destination.bit}]` : " · internal reset measurement"}</p>
            <p>Sampled value: {sample.outcome}</p>
            <p>Before sample: P(0) = {(sample.probabilities_before[0] * 100).toFixed(1)}% · P(1) = {(sample.probabilities_before[1] * 100).toFixed(1)}%</p>
            {checkpoint.kind === "reset" && <p>{sample.outcome === 1 ? "Applied X after collapse" : "No X needed"} · classical memory unchanged</p>}
          </div>)}
          <p className="text-slate-400">Samples are ordered; each probability is measured before that sample, after any earlier collapses. Post-operation state is shown below.</p>
        </div>}
        {checkpoint.outcome !== null && <p className="text-sm">Final shot outcome: {checkpoint.outcome}</p>}
        <h4 className="font-semibold text-sm">Checkpoint quantum state · q(n−1)…q0</h4>
        <QuantumStateTable key={`${trace.shot}-${current}`} label="Checkpoint quantum state" numQubits={debug.num_qubits} probabilities={checkpoint.quantum.probabilities} statevector={checkpoint.quantum.statevector} />
      </div>
    </div>
  </section>;
}
