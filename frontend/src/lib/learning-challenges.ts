import type { CircuitRequest, CircuitResult } from './api';
export type Check = { id: string; passed: boolean; message: string };
export type ValidationResult = {
  status: 'success' | 'near_miss' | 'incorrect' | 'invalid_circuit'; passed: boolean; score: number;
  checks: Check[]; feedback: { summary: string; details: string[]; explanation: string };
  hintsUsed: number; challengeId: string; moduleId: number; version: number;
};
export type Comparison = { matches: boolean; prediction: Record<string, number>; actual: Record<string, number>; ideal?: Record<string, number> | null; basis: string; tolerance: number };
export type Execution = { simulation: CircuitResult; idealProbabilities: Record<string,number> | null; comparison?: Comparison };
export type ChallengeDefinition = {
  id: string; moduleId: number; version: number; kind: 'circuit' | 'conceptual'; title: string;
  objective: string; instructions: string; reflection: string; initialState: string; starterCircuit: CircuitRequest;
  validationTypes: string[]; hintsAvailable: number;
  prediction: { kind: 'distribution' | 'answer'; labels: string[]; displayLabels: Record<string,string>; tolerance: number; prompt: string };
};
export type Attempt = { id: string; number: number; hintsUsed: number; score: number; passed: boolean; status: string; version: number };
export type ActivityDetail = { definition: ChallengeDefinition; completed: boolean; bestScore: number; history: Attempt[]; hints: string[]; workspace: { revision: string; circuit: CircuitRequest; prediction: Record<string,number>; execution: Execution | null; comparison: Comparison | null } | null };

export function circuitIdentity(circuit: CircuitRequest): string {
  return JSON.stringify({gates:circuit.gates,num_qubits:circuit.num_qubits,classical_registers:circuit.classical_registers ?? null,shots:circuit.shots ?? 1024});
}
export function validPrediction(labels: string[], values: Record<string,string>, distribution: boolean): boolean {
  const numbers=labels.map(k=>values[k]?.trim() ? Number(values[k]) : NaN);
  return numbers.every(Number.isFinite) && (distribution ? (numbers.every(v=>v>=0&&v<=1) && Math.abs(numbers.reduce((a,b)=>a+b,0)-1)<=1e-6) : numbers.every(v=>Number.isInteger(v)&&Math.abs(v)<=100000));
}

/** Runtime boundary: do not derive correctness from messages or trust an unchecked shape. */
export function parseValidationResult(value: unknown): ValidationResult {
  if (!value || typeof value !== 'object') throw new Error('Invalid activity feedback. Please reload.');
  const r=value as ValidationResult;
  if (!['success','near_miss','incorrect','invalid_circuit'].includes(r.status) || typeof r.passed!=='boolean' || r.passed!==(r.status==='success') || !Number.isInteger(r.score) || r.score<0 || r.score>100 || !Number.isInteger(r.moduleId) || !Number.isInteger(r.version) || typeof r.challengeId!=='string' || !Number.isInteger(r.hintsUsed) || !Array.isArray(r.checks) || !r.checks.every(c=>typeof c.id==='string'&&typeof c.passed==='boolean'&&typeof c.message==='string') || !r.feedback || typeof r.feedback.summary!=='string' || typeof r.feedback.explanation!=='string' || !Array.isArray(r.feedback.details) || !r.feedback.details.every(x=>typeof x==='string')) {
    throw new Error('Invalid activity feedback. Please reload.');
  }
  return r;
}
