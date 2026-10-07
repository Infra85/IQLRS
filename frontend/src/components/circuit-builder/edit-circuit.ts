import type { Gate } from "../../lib/api";

export type GateDragSource = {
  type: string;
  index?: number;
  anchorQubit?: number;
  theta?: number;
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
    if (!PALETTE.includes(source.type as PaletteGate) || isLinked(source.type)) return null;
    gate = makeGate(source.type, target.qubit, undefined, source.theta ?? Math.PI / 2);
  } else {
    const original = gates[source.index];
    if (!original) return null;
    if (isLinked(original.type)) {
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
    } else gate = original.type === "MEASURE_ALL" ? { ...original } : { ...original, qubit: target.qubit };
  }
  const next = gates.filter((_, i) => i !== source.index);
  const column = Math.max(0, Math.min(gates.length, target.column));
  const insertion =
    source.index !== undefined && source.index < column ? column - 1 : column;
  next.splice(insertion, 0, gate);
  return next;
}


export const PALETTE = ["I", "H", "X", "Y", "Z", "S", "T", "RX", "RY", "RZ", "CNOT", "CY", "CZ", "CH", "CRX", "CRY", "CRZ", "SWAP", "MEASURE", "MEASURE_ALL", "RESET"] as const;
export type PaletteGate = (typeof PALETTE)[number];
export const isLinked = (type: string) => ["CNOT", "CX", "CY", "CZ", "CH", "CRX", "CRY", "CRZ", "SWAP"].includes(type);
export const isRotation = (type: string) => /^(C)?R[XYZ]$/.test(type);

/** Small, non-evaluating angle grammar: radians, pi, -pi/2, 3*pi/4. */
export function parseAngle(input: string): number {
  const text = input.trim().toLowerCase().replace(/π/g, "pi").replace(/\s/g, "");
  const match = text.match(/^([+-]?(?:\d+(?:\.\d*)?|\.\d+)?)\*?pi(?:\/([+-]?(?:\d+(?:\.\d*)?|\.\d+)))?$/);
  const value = match
    ? (match[1] === "-" ? -1 : match[1] === "+" || match[1] === "" ? 1 : Number(match[1])) * Math.PI / (match[2] ? Number(match[2]) : 1)
    : text ? Number(text) : NaN;
  if (!Number.isFinite(value)) throw new Error("Theta must be finite radians, for example 1.5708, pi/2, or -pi.");
  return value;
}

export function makeGate(type: string, qubit: number, control?: number, theta = Math.PI / 2): Gate {
  const gate: Gate = type === "MEASURE_ALL" ? { type } : isLinked(type)
    ? { type, control, target: qubit } : { type, qubit };
  if (isRotation(type)) {
    if (!Number.isFinite(theta)) throw new Error("Theta must be a finite number.");
    gate.params = { theta };
  }
  return gate;
}

export function validateCircuit(gates: Gate[], numQubits: number): void {
  if (gates.length > 500) throw new Error("Use at most 500 operations.");
  for (const gate of gates) {
    if (!PALETTE.includes(gate.type as PaletteGate)) throw new Error(`Unsupported gate: ${gate.type}`);
    const indices = gate.type === "MEASURE_ALL" ? [] : isLinked(gate.type) ? [gate.control, gate.target] : [gate.qubit];
    if (indices.some(q => q == null || !Number.isInteger(q) || q < 0 || q >= numQubits)) throw new Error(`${gate.type}: select valid qubits.`);
    if (new Set(indices).size !== indices.length) throw new Error("Choose distinct qubits.");
    if (isRotation(gate.type) && !Number.isFinite(gate.params?.theta)) throw new Error(`${gate.type}: theta must be finite radians.`);
  }
}
