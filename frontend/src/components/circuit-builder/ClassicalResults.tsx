"use client";

import type { CircuitResult } from "@/lib/api";
import { referenceLabel } from "./classical-circuit";

export function ClassicalResults({ result }: { result: CircuitResult }) {
  return <div className="panel p-5 lg:col-span-2 space-y-4">
    <h2 className="section-title">Classical register result</h2>
    <p className="text-sm text-slate-400">Last shot, highest bit first within each register. Memory starts at zero; measurement history identifies writes.</p>
    <div className="flex flex-wrap gap-4 font-mono text-sm">
      {Object.entries(result.last_classical ?? {}).map(([name, bits]) => <span key={name}>{name} = {bits}</span>)}
    </div>
    <p className="text-sm">Measured bit order: {result.classical_bit_order?.map(referenceLabel).join(", ") || "No explicit measurements"}</p>
    <details>
      <summary className="cursor-pointer">Per-shot results ({result.shot_results?.length ?? 0} recorded)</summary>
      {!result.shot_results?.length && <p className="mt-3 text-sm">Enable shot history before running to inspect individual shots.</p>}
      {!!result.shot_results?.length && <>
        <p className="mt-3 text-sm text-slate-400">First {result.shot_results.length} shots of {result.metadata?.shots}. Counts aggregate all shots. The statevector below describes the last shot.</p>
        <ol className="mt-3 max-h-96 overflow-auto space-y-3 text-sm">
          {result.shot_results.map(shot => <li key={shot.shot} className="border-b border-white/10 pb-3">
            <p className="font-mono">Shot {shot.shot}: {shot.outcome} · {Object.entries(shot.classical).map(([name, bits]) => `${name} = ${bits}`).join(" · ")}</p>
            <ol className="mt-1 space-y-1">
              {shot.measurements.map(m => <li key={m.operation}>
                Operation {m.operation + 1}: {m.qubits.map((q, i) => `q${q} → ${m.destinations?.[i] ? referenceLabel(m.destinations[i]) : "readout"} = ${m.bits[i]}`).join("; ")}
              </li>)}
            </ol>
          </li>)}
        </ol>
      </>}
    </details>
  </div>;
}
