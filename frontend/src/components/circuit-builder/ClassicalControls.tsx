"use client";

import type { ClassicalRegister, Gate } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { classicalBits, conditionLabel, isMeasurement, measurementTargets, referenceKey, referenceLabel, setMeasurementDestination } from "./classical-circuit";

type Props = {
  registers: ClassicalRegister[] | undefined;
  gates: Gate[];
  numQubits: number;
  onRegisters: (registers: ClassicalRegister[] | undefined) => void;
  onRename: (index: number, name: string) => void;
  onGate: (index: number, gate: Gate) => void;
};

export function ClassicalControls({ registers, gates, numQubits, onRegisters, onRename, onGate }: Props) {
  const bits = classicalBits(registers ?? []);
  const used = (name: string) => gates.some(g => g.condition?.register === name || g.destinations?.some(d => d.register === name));
  return <section className="panel p-6 space-y-4" aria-label="Classical control configuration">
    <h2 className="section-title">Classical registers and conditions</h2>
    <label className="flex items-center gap-3 text-sm">
      <input type="checkbox" checked={!!registers} disabled={!!registers && gates.some(g => g.condition || g.destinations)}
        onChange={e => onRegisters(e.target.checked ? [{ name: "c", size: numQubits }] : undefined)} />
      Enable classical registers
    </label>
    <p className="text-sm text-slate-400">Measurements write classical bits; IF conditions read them. Quantum control dots still refer to qubits. Remove mapped operations before disabling classical registers.</p>
    {registers && <>
      <div className="space-y-3">
        {registers.map((r, i) => <div key={i} className="flex flex-wrap items-end gap-3">
          <label className="text-sm">Register {i + 1} name
            <Input aria-label={`Register ${i + 1} name`} key={`${i}-${r.name}`} defaultValue={r.name} maxLength={32} onBlur={e => { onRename(i, e.target.value); e.target.value = r.name; }} />
          </label>
          <label className="text-sm">Size
            <Input aria-label={`Register ${i + 1} size`} type="number" min={1} max={32} value={Number.isNaN(r.size) ? "" : r.size}
              onChange={e => onRegisters(registers.map((item, index) => index === i ? { ...item, size: e.target.valueAsNumber } : item))} />
          </label>
          <button type="button" className="ui-button button-secondary" disabled={registers.length === 1 || used(r.name)}
            onClick={() => onRegisters(registers.filter((_, index) => index !== i))}>Remove register {i + 1}</button>
        </div>)}
        <button type="button" className="ui-button button-secondary" disabled={registers.length >= 8} onClick={() => {
          let index = registers.length;
          while (registers.some(r => r.name === `c${index}`)) index++;
          onRegisters([...registers, { name: `c${index}`, size: 1 }]);
        }}>Add classical register</button>
      </div>
      <p className="text-sm text-slate-400">Every shot initializes all bits to 0. Unwritten bits can be tested. Counts show mapped bits only; x means a conditional measurement did not write that bit.</p>
      {gates.map((gate, index) => <div key={index} className="rounded border border-white/10 p-3 space-y-3">
        <p className="text-sm font-semibold">Operation {index + 1}: {gate.type} {conditionLabel(gate)}</p>
        {isMeasurement(gate) && measurementTargets(gate, numQubits).map((qubit, destinationIndex) => <label key={qubit} className="flex flex-wrap items-center gap-3 text-sm">
          Measure q{qubit} →
          <select className="ui-input max-w-full" aria-label={`Operation ${index + 1} q${qubit} destination`}
            value={gate.destinations?.[destinationIndex] && bits.some(b => referenceKey(b) === referenceKey(gate.destinations![destinationIndex])) ? referenceKey(gate.destinations[destinationIndex]) : ""}
            onChange={e => {
              const ref = bits.find(b => referenceKey(b) === e.target.value);
              if (!ref) return;
              onGate(index, setMeasurementDestination(gate, destinationIndex, ref, numQubits));
            }}>
            <option value="" disabled>Choose classical bit</option>
            {bits.map(b => <option key={referenceKey(b)} value={referenceKey(b)}>{referenceLabel(b)}</option>)}
          </select>
        </label>)}
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-sm">Classical condition
            <select className="ui-input max-w-full" aria-label={`Operation ${index + 1} classical condition`}
              value={gate.condition ? `${gate.condition.register}:${gate.condition.bit ?? "*"}` : ""}
              onChange={e => {
                if (!e.target.value) { const next = { ...gate }; delete next.condition; onGate(index, next); return; }
                const [register, bit] = e.target.value.split(":");
                onGate(index, { ...gate, condition: { register, bit: bit === "*" ? null : Number(bit), operator: "eq", value: bit === "*" ? 0 : 1 } });
              }}>
              <option value="">Always execute</option>
              {bits.map(b => <option key={referenceKey(b)} value={referenceKey(b)}>IF {referenceLabel(b)}</option>)}
              {registers.map(r => <option key={r.name} value={`${r.name}:*`}>IF register {r.name}</option>)}
            </select>
          </label>
          {gate.condition && <label className="text-sm">equals
            <Input className="w-24" aria-label={`Operation ${index + 1} condition value`} type="number" min={0}
              value={Number.isNaN(gate.condition.value) ? "" : gate.condition.value}
              onChange={e => onGate(index, { ...gate, condition: { ...gate.condition!, value: e.target.valueAsNumber } })} />
          </label>}
        </div>
      </div>)}
    </>}
  </section>;
}
