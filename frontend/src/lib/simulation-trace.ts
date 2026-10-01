import type { ClassicalBit, ClassicalCondition, Gate } from "./api";

export type DebugRequest = {
  enabled: boolean;
  shot_numbers: number[];
  checkpoint_mode: "all" | "selected";
  operation_indices?: number[];
  include_statevector: boolean;
};
export type TraceOperation = {
  type: string; targets: number[]; controls: number[]; params: Record<string, number>;
  condition: ClassicalCondition | null; destinations: ClassicalBit[] | null;
};
export type ExecutionCheckpoint = {
  kind: "start" | "end" | "operation" | "measurement" | "condition" | "reset";
  operation_index: number | null;
  executed: boolean | null;
  quantum: { probabilities: number[]; statevector: number[][] | null };
  classical: Record<string, string>;
  condition: { actual: number; expected: number; matched: boolean } | null;
  samples: { qubit: number; destination: ClassicalBit | null; outcome: number; probabilities_before: number[] }[];
  outcome: string | null;
};
export type DebugResult = {
  version: 1; num_qubits: number; shot_numbering: "one_based"; operation_indexing: "zero_based";
  operations: Record<string, TraceOperation>;
  traces: { shot: number; checkpoints: ExecutionCheckpoint[] }[];
};
export type DebugSettings = { enabled: boolean; shots: string; mode: "all" | "selected"; operations: string; amplitudes: boolean };
export const initialDebugSettings: DebugSettings = { enabled: false, shots: "1", mode: "all", operations: "1", amplitudes: false };

function numbers(input: string, maximum: number, limit: number, label: string): number[] {
  const tokens = input.split(",").map(t => t.trim());
  if (!tokens.length || tokens.length > limit || tokens.some(t => !/^\d+$/.test(t))) throw new Error(`${label}: enter 1–${limit} comma-separated positive integers.`);
  const values = tokens.map(Number);
  if (values.some(v => !Number.isSafeInteger(v) || v < 1 || v > maximum)) throw new Error(`${label}: use numbers from 1 to ${maximum}.`);
  if (new Set(values).size !== values.length) throw new Error(`${label}: duplicate numbers are not allowed.`);
  return values;
}

export function makeDebugRequest(settings: DebugSettings, shots: number, gates: Gate[], numQubits: number): DebugRequest | undefined {
  if (!settings.enabled) return undefined;
  const selectedShots = numbers(settings.shots, shots, 16, "Debug shots");
  const indices = settings.mode === "selected" ? numbers(settings.operations, gates.length, 254, "Debug operations").map(i => i - 1) : undefined;
  const selected = new Set(indices ?? gates.map((_, i) => i));
  gates.forEach((g, i) => { if (g.condition || ["MEASURE", "MEASURE_ALL", "RESET"].includes(g.type)) selected.add(i); });
  const perShot = selected.size + 2;
  const total = perShot * selectedShots.length;
  if (perShot > 256 || total > 512 || total * 2 ** numQubits > 32768) throw new Error("Debug checkpoint budget exceeded. Select fewer shots or ordinary operations.");
  if (settings.amplitudes && total > 64) throw new Error("Debug amplitudes allow at most 64 snapshots. Disable amplitudes or select fewer checkpoints.");
  return { enabled: true, shot_numbers: selectedShots, checkpoint_mode: settings.mode, operation_indices: indices, include_statevector: settings.amplitudes };
}

export function stepCheckpoint(current: number, delta: number, count: number): number {
  return Math.max(0, Math.min(count - 1, current + delta));
}
export function operationLabel(operation: TraceOperation): string {
  const params = operation.params.theta !== undefined ? `(${operation.params.theta.toFixed(4)})` : "";
  let label = `${operation.type}${params} ${operation.targets.map(q => `q${q}`).join(", ")}`;
  if (operation.controls.length) label += ` · quantum control ${operation.controls.map(q => `q${q}`).join(", ")}`;
  if (operation.destinations) label += ` → ${operation.destinations.map(d => `${d.register}[${d.bit}]`).join(", ")}`;
  const c = operation.condition;
  if (c) label += ` IF ${c.register}${c.bit == null ? "" : `[${c.bit}]`} == ${c.value}`;
  return label;
}
export function checkpointStatus(checkpoint: ExecutionCheckpoint): string {
  if (checkpoint.kind === "start") return "INITIAL STATE";
  if (checkpoint.kind === "end") return "COMPLETE";
  return checkpoint.executed ? "EXECUTED" : "SKIPPED";
}
