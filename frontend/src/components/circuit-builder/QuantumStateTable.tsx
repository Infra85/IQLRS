"use client";
import { useState } from "react";

export function QuantumStateTable({ probabilities, statevector, numQubits, label = "Quantum state" }: {
  probabilities: number[]; statevector?: number[][] | null; numQubits: number; label?: string;
}) {
  const [page, setPage] = useState(0);
  const pageCount = Math.max(1, Math.ceil(probabilities.length / 32));
  const current = Math.min(page, pageCount - 1);
  const start = current * 32;
  return <div role="region" aria-label={label}>
    <ul className="result-list mt-4 space-y-2 font-mono text-xs text-slate-300">
      {probabilities.slice(start, start + 32).map((p, offset) => {
        const index = start + offset;
        const pair = statevector?.[index];
        return <li key={index} className="flex flex-wrap justify-between gap-x-4 gap-y-1 border-b border-white/5 py-1">
          <span>|{index.toString(2).padStart(numQubits, "0")}⟩</span>
          <span>{pair && `${pair[0].toFixed(3)} ${pair[1] >= 0 ? "+" : "-"}${Math.abs(pair[1]).toFixed(3)}i `}<span className="text-slate-400">p={p.toFixed(3)}</span></span>
        </li>;
      })}
    </ul>
    {pageCount > 1 && <div className="mt-3 flex flex-wrap gap-3 items-center text-sm">
      <button type="button" className="ui-button button-secondary" disabled={current === 0} onClick={() => setPage(current - 1)}>Previous basis page</button>
      <span>Basis page {current + 1} of {pageCount}</span>
      <button type="button" className="ui-button button-secondary" disabled={current === pageCount - 1} onClick={() => setPage(current + 1)}>Next basis page</button>
    </div>}
  </div>;
}
