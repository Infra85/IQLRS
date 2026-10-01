import type { ClassicalBit, ClassicalRegister, Gate } from "../../lib/api";

export const isMeasurement = (gate: Gate) => ["MEASURE", "MEASURE_ALL"].includes(gate.type);
export const referenceLabel = (ref: ClassicalBit) => `${ref.register}[${ref.bit}]`;
export const referenceKey = (ref: ClassicalBit) => `${ref.register}:${ref.bit}`;

export function classicalBits(registers: ClassicalRegister[]): ClassicalBit[] {
  return registers.flatMap(r => Array.from({ length: Math.max(0, Math.min(32, r.size || 0)) }, (_, bit) => ({ register: r.name, bit })));
}

export function measurementTargets(gate: Gate, numQubits: number): number[] {
  if (!isMeasurement(gate)) return [];
  return gate.type === "MEASURE_ALL" ? Array.from({ length: numQubits }, (_, q) => q) : gate.targets ?? [gate.qubit!];
}

export function withDefaultDestinations(gate: Gate, registers: ClassicalRegister[] | undefined, numQubits: number): Gate {
  if (!registers || !isMeasurement(gate) || gate.destinations) return gate;
  const bits = classicalBits(registers);
  const targets = measurementTargets(gate, numQubits);
  return { ...gate, destinations: targets.map(q => bits[q]).filter((b): b is ClassicalBit => !!b) };
}

export function setMeasurementDestination(gate: Gate, index: number, ref: ClassicalBit, numQubits: number): Gate {
  // Keep missing selections explicit; sparse arrays can bypass validation or crash editors.
  const destinations = measurementTargets(gate, numQubits).map((_, i) =>
    i === index ? ref : gate.destinations?.[i] ?? { register: "", bit: -1 });
  return { ...gate, destinations };
}

export function conditionLabel(gate: Gate): string {
  const c = gate.condition;
  if (!c) return "";
  return `IF ${c.register}${c.bit == null ? "" : `[${c.bit}]`} == ${c.value}`;
}

export function validateClassicalCircuit(gates: Gate[], registers: ClassicalRegister[] | undefined, numQubits: number): void {
  if (!registers) return;
  const sizes = new Map<string, number>();
  if (!registers.length || registers.length > 8) throw new Error("Use 1–8 classical registers.");
  for (const r of registers) {
    if (!/^[A-Za-z][A-Za-z0-9_]{0,31}$/.test(r.name)) throw new Error("Register names must start with a letter and use up to 32 letters, digits or underscores.");
    if (sizes.has(r.name)) throw new Error("Register names must be unique.");
    if (!Number.isInteger(r.size) || r.size < 1 || r.size > 32) throw new Error("Register sizes must be integers from 1 to 32.");
    sizes.set(r.name, r.size);
  }
  if (registers.reduce((sum, r) => sum + r.size, 0) > 32) throw new Error("Use at most 32 classical bits.");
  const validBit = (ref: ClassicalBit) => sizes.has(ref.register) && Number.isInteger(ref.bit) && ref.bit >= 0 && ref.bit < sizes.get(ref.register)!;
  for (const [i, gate] of gates.entries()) {
    if (isMeasurement(gate)) {
      const refs = gate.destinations;
      if (!refs || refs.length !== measurementTargets(gate, numQubits).length || !measurementTargets(gate, numQubits).every((_, j) => refs[j] && validBit(refs[j]))) throw new Error(`Operation ${i + 1}: choose a valid destination for every measured qubit.`);
      if (new Set(refs.map(referenceKey)).size !== refs.length) throw new Error(`Operation ${i + 1}: measurement destinations must be distinct.`);
    }
    const c = gate.condition;
    if (c) {
      const size = sizes.get(c.register);
      if (size === undefined || (c.bit != null && !validBit({ register: c.register, bit: c.bit }))) throw new Error(`Operation ${i + 1}: choose an existing classical condition reference.`);
      if (c.operator !== "eq" || !Number.isInteger(c.value) || c.value < 0 || c.value >= (c.bit == null ? 2 ** size : 2)) throw new Error(`Operation ${i + 1}: condition value is outside the selected bit/register range.`);
    }
  }
}
