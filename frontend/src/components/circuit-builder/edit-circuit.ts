import type { Gate } from "../../lib/api";

export type GateDragSource = {
  type: string;
  index?: number;
  anchorQubit?: number;
};
export type GateDropTarget = { qubit: number; column: number };

/** Drop before the addressed column; an end-wire drop appends an operation. */
export function dropGate(
  gates: Gate[],
  source: GateDragSource,
  target: GateDropTarget,
  numQubits: number,
): Gate[] | null {
  if (
    !Number.isInteger(target.qubit) ||
    target.qubit < 0 ||
    target.qubit >= numQubits
  )
    return null;
  let gate: Gate;
  if (source.index === undefined) {
    if (!["H", "X", "Y", "Z"].includes(source.type)) return null;
    gate = { type: source.type, qubit: target.qubit };
  } else {
    const original = gates[source.index];
    if (!original) return null;
    if (original.type === "CNOT") {
      if (
        original.control == null ||
        original.target == null ||
        source.anchorQubit == null
      )
        return null;
      const delta = target.qubit - source.anchorQubit;
      const control = original.control + delta;
      const end = original.target + delta;
      if (Math.min(control, end) < 0 || Math.max(control, end) >= numQubits)
        return null;
      gate = { ...original, control, target: end };
    } else gate = { ...original, qubit: target.qubit };
  }
  const next = gates.filter((_, i) => i !== source.index);
  const column = Math.max(0, Math.min(gates.length, target.column));
  const insertion =
    source.index !== undefined && source.index < column ? column - 1 : column;
  next.splice(insertion, 0, gate);
  return next;
}
