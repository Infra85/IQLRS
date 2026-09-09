"use client";

import { useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  simulateCircuit,
  type CircuitResult,
  type Gate,
} from "@/lib/api";

const PALETTE = ["H", "X", "Y", "Z", "CNOT"] as const;
type PaletteGate = (typeof PALETTE)[number];

const CHALLENGES = {
  bell: {
    title: "Bell State challenge",
    instructions: "Starting from |00⟩, place H on q0, then CNOT with q0 as control and q1 as target. The simulator must produce |Φ+⟩ = (|00⟩ + |11⟩)/√2.",
    gates: [{ type: "H", qubit: 0 }, { type: "CNOT", control: 0, target: 1 }] as Gate[],
  },
  grover: {
    title: "Grover 2-qubit challenge",
    instructions: "Build a two-qubit Grover search circuit for the marked state |11⟩. A successful simulated state has all probability on |11⟩. You can load the guided circuit to inspect and run it.",
    gates: [
      { type: "H", qubit: 0 }, { type: "H", qubit: 1 }, { type: "H", qubit: 1 },
      { type: "CNOT", control: 0, target: 1 }, { type: "H", qubit: 1 },
      { type: "H", qubit: 0 }, { type: "H", qubit: 1 }, { type: "X", qubit: 0 },
      { type: "X", qubit: 1 }, { type: "H", qubit: 1 }, { type: "CNOT", control: 0, target: 1 },
      { type: "H", qubit: 1 }, { type: "X", qubit: 0 }, { type: "X", qubit: 1 },
      { type: "H", qubit: 0 }, { type: "H", qubit: 1 },
    ] as Gate[],
  },
} as const;

const GATE_STYLES: Record<string, string> = {
  H: "bg-quantum-600 border-quantum-400",
  X: "bg-rose-600 border-rose-400",
  Y: "bg-amber-600 border-amber-400",
  Z: "bg-emerald-600 border-emerald-400",
  CNOT: "bg-violet-600 border-violet-400",
};

function formatAmplitude(pair: number[]): string {
  const [re, im] = pair;
  const rePart = re.toFixed(3);
  const imPart = `${im >= 0 ? "+" : "-"}${Math.abs(im).toFixed(3)}i`;
  return `${rePart} ${imPart}`;
}

function probability(pair: number[]): number {
  return pair[0] * pair[0] + pair[1] * pair[1];
}

export default function CircuitBuilder() {
  const searchParams = useSearchParams();
  const challengeKey = searchParams.get("challenge") as keyof typeof CHALLENGES | null;
  const challenge = challengeKey ? CHALLENGES[challengeKey] : undefined;
  const [numQubits, setNumQubits] = useState(2);
  const [shots, setShots] = useState(1024);
  const [gates, setGates] = useState<Gate[]>([]);
  const [selected, setSelected] = useState<PaletteGate | null>("H");
  const [cnotControl, setCnotControl] = useState<number | null>(null);
  const [result, setResult] = useState<CircuitResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [challengeStatus, setChallengeStatus] = useState<string | null>(null);

  const maxCount = useMemo(() => {
    if (!result) return 1;
    return Math.max(1, ...Object.values(result.counts));
  }, [result]);

  function changeQubits(next: number) {
    const clamped = Math.min(10, Math.max(1, next));
    setNumQubits(clamped);
    setGates((current) =>
      current.filter((gate) => {
        const indices = [gate.qubit, gate.control, gate.target].filter(
          (value): value is number => value !== undefined && value !== null
        );
        return indices.every((index) => index < clamped);
      })
    );
    setCnotControl(null);
    setResult(null);
  }

  function placeOnQubit(qubit: number) {
    if (!selected) return;
    if (selected === "CNOT") {
      if (cnotControl === null) {
        setCnotControl(qubit);
        return;
      }
      if (cnotControl === qubit) {
        setCnotControl(null);
        return;
      }
      setGates((current) => [
        ...current,
        { type: "CNOT", control: cnotControl, target: qubit },
      ]);
      setCnotControl(null);
      setResult(null);
      return;
    }
    setGates((current) => [...current, { type: selected, qubit }]);
    setResult(null);
  }

  function removeGate(index: number) {
    setGates((current) => current.filter((_, i) => i !== index));
    setResult(null);
  }

  function clearCircuit() {
    setGates([]);
    setCnotControl(null);
    setResult(null);
    setError(null);
    setChallengeStatus(null);
  }

  function loadChallengeCircuit() {
    if (!challenge) return;
    setNumQubits(2);
    setGates(challenge.gates);
    setResult(null);
    setChallengeStatus(null);
  }

  async function onSimulate() {
    setLoading(true);
    setError(null);
    try {
      const data = await simulateCircuit({
        gates,
        num_qubits: numQubits,
        shots,
        backend: "qiskit",
      });
      setResult(data);
      if (challengeKey === "bell") {
        const p00 = data.statevector ? probability(data.statevector[0]) : 0;
        const p11 = data.statevector ? probability(data.statevector[3]) : 0;
        const conceptualCircuit = gates.length === 2 && gates[0].type === "H" && gates[0].qubit === 0 && gates[1].type === "CNOT" && gates[1].control === 0 && gates[1].target === 1;
        setChallengeStatus(conceptualCircuit && Math.abs(p00 - 0.5) < 1e-9 && Math.abs(p11 - 0.5) < 1e-9 ? "Challenge complete: your required H → CNOT circuit simulated the Bell state |Φ+⟩." : "Not complete yet: use exactly H on q0 followed by CNOT control q0 → target q1, then simulate.");
      } else if (challengeKey === "grover") {
        const p11 = data.statevector ? probability(data.statevector[3]) : 0;
        setChallengeStatus(numQubits === 2 && p11 > 0.999999 ? "Challenge complete: simulation concentrates probability on the marked state |11⟩." : `Keep refining the circuit: the simulator reports P(|11⟩) = ${(p11 * 100).toFixed(1)}%.`);
      }
    } catch (err) {
      setResult(null);
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mt-8 space-y-8">
      {challenge && <section className="rounded-xl border border-quantum-700 bg-quantum-950/30 p-5"><h2 className="text-xl font-semibold">{challenge.title}</h2><p className="mt-2 text-sm leading-6 text-gray-300">{challenge.instructions}</p><button type="button" onClick={loadChallengeCircuit} className="mt-4 rounded-lg border border-quantum-400 px-4 py-2 text-sm font-medium text-quantum-200 hover:bg-quantum-900">Load guided circuit</button>{challengeStatus && <p className={`mt-4 rounded-lg p-3 text-sm ${challengeStatus.startsWith("Challenge complete") ? "bg-green-950/50 text-green-200" : "bg-amber-950/50 text-amber-200"}`}>{challengeStatus}</p>}</section>}
      <section className="flex flex-wrap items-end gap-6">
        <label className="flex flex-col gap-2 text-sm text-gray-300">
          Qubits
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="h-9 w-9 rounded-md border border-gray-700 bg-gray-900 hover:bg-gray-800"
              onClick={() => changeQubits(numQubits - 1)}
            >
              −
            </button>
            <span className="w-8 text-center text-lg font-semibold text-white">
              {numQubits}
            </span>
            <button
              type="button"
              className="h-9 w-9 rounded-md border border-gray-700 bg-gray-900 hover:bg-gray-800"
              onClick={() => changeQubits(numQubits + 1)}
            >
              +
            </button>
          </div>
        </label>
        <label className="flex flex-col gap-2 text-sm text-gray-300">
          Shots
          <input
            type="number"
            min={1}
            max={8192}
            value={shots}
            onChange={(event) =>
              setShots(Math.min(8192, Math.max(1, Number(event.target.value) || 1)))
            }
            className="h-9 w-28 rounded-md border border-gray-700 bg-gray-900 px-3 text-white"
          />
        </label>
      </section>

      <section>
        <p className="mb-3 text-sm text-gray-400">Gate palette</p>
        <div className="flex flex-wrap gap-2">
          {PALETTE.map((gate) => (
            <button
              key={gate}
              type="button"
              onClick={() => {
                setSelected((current) => (current === gate ? null : gate));
                setCnotControl(null);
              }}
              className={`rounded-md border px-4 py-2 font-mono text-sm font-semibold transition ${
                GATE_STYLES[gate]
              } ${selected === gate ? "ring-2 ring-white" : "opacity-80 hover:opacity-100"}`}
            >
              {gate}
            </button>
          ))}
        </div>
        <p className="mt-3 text-sm text-gray-500">
          {selected === "CNOT"
            ? cnotControl === null
              ? "CNOT selected — click a qubit wire for the control, then the target."
              : `Control is q${cnotControl} — click a different qubit for the target.`
            : selected
              ? `${selected} selected — click a qubit wire to place it.`
              : "Select a gate, then click a qubit wire. Click a placed gate to remove it."}
        </p>
      </section>

      <section className="overflow-x-auto rounded-xl border border-gray-800 bg-gray-900/60 p-6">
        <div
          className="grid items-center gap-x-2 gap-y-4"
          style={{
            gridTemplateColumns: `auto repeat(${Math.max(gates.length, 1)}, minmax(3.5rem, auto)) auto`,
          }}
        >
          {Array.from({ length: numQubits }, (_, qubit) => (
            <QubitRow
              key={qubit}
              qubit={qubit}
              gates={gates}
              cnotControl={cnotControl}
              onPlace={() => placeOnQubit(qubit)}
              onRemove={removeGate}
            />
          ))}
        </div>
      </section>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onSimulate}
          disabled={loading}
          className="rounded-lg bg-quantum-600 px-5 py-2.5 font-medium transition hover:bg-quantum-700 disabled:opacity-60"
        >
          {loading ? "Simulating…" : "Simulate"}
        </button>
        <button
          type="button"
          onClick={clearCircuit}
          className="rounded-lg border border-gray-700 px-5 py-2.5 font-medium transition hover:bg-gray-800"
        >
          Clear circuit
        </button>
      </div>

      {error && (
        <p className="rounded-lg border border-red-800 bg-red-950/60 px-4 py-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {result && (
        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5">
            <h2 className="text-lg font-semibold">Measurement counts</h2>
            <ul className="mt-4 space-y-2">
              {Object.entries(result.counts)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([bitstring, count]) => (
                  <li key={bitstring} className="flex items-center gap-3 text-sm">
                    <span className="w-16 font-mono text-gray-300">|{bitstring}⟩</span>
                    <div className="h-3 flex-1 overflow-hidden rounded bg-gray-800">
                      <div
                        className="h-full bg-quantum-500"
                        style={{ width: `${(count / maxCount) * 100}%` }}
                      />
                    </div>
                    <span className="w-24 text-right text-gray-400">
                      {count} ({((count / shots) * 100).toFixed(1)}%)
                    </span>
                  </li>
                ))}
            </ul>
          </div>

          <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5">
            <h2 className="text-lg font-semibold">Statevector</h2>
            {result.statevector ? (
              <ul className="mt-4 space-y-1 font-mono text-sm text-gray-300">
                {result.statevector.map((pair, index) => (
                  <li key={index} className="flex justify-between gap-4">
                    <span>
                      |{index.toString(2).padStart(numQubits, "0")}⟩
                    </span>
                    <span>
                      {formatAmplitude(pair)}{" "}
                      <span className="text-gray-500">
                        p={probability(pair).toFixed(3)}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-gray-500">No statevector returned.</p>
            )}
          </div>

          {result.circuit_diagram && (
            <div className="rounded-xl border border-gray-800 bg-gray-900/60 p-5 lg:col-span-2">
              <h2 className="text-lg font-semibold">Circuit diagram</h2>
              <pre className="mt-3 overflow-x-auto text-sm text-gray-300">
                {result.circuit_diagram}
              </pre>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

function QubitRow({
  qubit,
  gates,
  cnotControl,
  onPlace,
  onRemove,
}: {
  qubit: number;
  gates: Gate[];
  cnotControl: number | null;
  onPlace: () => void;
  onRemove: (index: number) => void;
}) {
  return (
    <>
      <button
        type="button"
        onClick={onPlace}
        className={`w-14 rounded-md px-2 py-1 text-left font-mono text-sm ${
          cnotControl === qubit
            ? "bg-violet-900 text-violet-200"
            : "text-gray-400 hover:bg-gray-800 hover:text-white"
        }`}
      >
        q{qubit}
      </button>
      {(gates.length === 0 ? [null] : gates).map((gate, index) => {
        if (gate === null) {
          return (
            <button
              key="empty"
              type="button"
              onClick={onPlace}
              className="relative h-12 min-w-[3.5rem]"
            >
              <span className="absolute inset-x-0 top-1/2 h-px bg-gray-700" />
            </button>
          );
        }
        return (
          <GateCell
            key={`${index}-${gate.type}`}
            gate={gate}
            qubit={qubit}
            onPlace={onPlace}
            onRemove={() => onRemove(index)}
          />
        );
      })}
      <button
        type="button"
        onClick={onPlace}
        className="relative h-12 min-w-[2rem] flex-1"
        aria-label={`Place gate on qubit ${qubit}`}
      >
        <span className="absolute inset-x-0 top-1/2 h-px bg-gray-700" />
      </button>
    </>
  );
}

function GateCell({
  gate,
  qubit,
  onPlace,
  onRemove,
}: {
  gate: Gate;
  qubit: number;
  onPlace: () => void;
  onRemove: () => void;
}) {
  const isCnot = gate.type === "CNOT";
  const involved = isCnot
    ? gate.control === qubit || gate.target === qubit
    : gate.qubit === qubit;

  if (!involved) {
    const betweenCnot =
      isCnot &&
      gate.control !== null &&
      gate.control !== undefined &&
      gate.target !== null &&
      gate.target !== undefined &&
      qubit > Math.min(gate.control, gate.target) &&
      qubit < Math.max(gate.control, gate.target);

    return (
      <button
        type="button"
        onClick={onPlace}
        className="relative flex h-12 min-w-[3.5rem] items-center justify-center"
      >
        <span className="absolute inset-x-0 top-1/2 h-px bg-gray-700" />
        {betweenCnot && <span className="absolute h-12 w-px bg-violet-400" />}
      </button>
    );
  }

  if (isCnot) {
    const isControl = gate.control === qubit;
    return (
      <button
        type="button"
        onClick={onRemove}
        title="Remove CNOT"
        className="relative flex h-12 min-w-[3.5rem] items-center justify-center"
      >
        <span className="absolute inset-x-0 top-1/2 h-px bg-gray-700" />
        <span className="absolute h-12 w-px bg-violet-400" />
        {isControl ? (
          <span className="relative z-10 h-3 w-3 rounded-full bg-violet-400" />
        ) : (
          <span className="relative z-10 flex h-6 w-6 items-center justify-center rounded-full border-2 border-violet-300 text-xs text-violet-200">
            ⊕
          </span>
        )}
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={onRemove}
      title={`Remove ${gate.type}`}
      className="relative flex h-12 min-w-[3.5rem] items-center justify-center"
    >
      <span className="absolute inset-x-0 top-1/2 h-px bg-gray-700" />
      <span
        className={`relative z-10 flex h-9 w-9 items-center justify-center rounded-md border font-mono text-sm font-bold ${
          GATE_STYLES[gate.type] ?? "bg-gray-700 border-gray-500"
        }`}
      >
        {gate.type}
      </span>
    </button>
  );
}
