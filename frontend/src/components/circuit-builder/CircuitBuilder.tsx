"use client";

import { ListenButton } from "@/components/narration/provider";
import { Button } from "@/components/ui/button";
import { Status, EmptyState } from "@/components/ui/page";
import { Input } from "@/components/ui/input";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import {
  dropGate,
  type GateDragSource,
  type GateDropTarget,
} from "./edit-circuit";
import { useGateDrag } from "./use-gate-drag";
import { useSearchParams } from "next/navigation";
import { simulateCircuit, type CircuitResult, type Gate } from "@/lib/api";

const PALETTE = ["H", "X", "Y", "Z", "CNOT"] as const;
type PaletteGate = (typeof PALETTE)[number];

const CHALLENGES = {
  bell: {
    title: "Bell State challenge",
    instructions:
      "Starting from |00⟩, place H on q0, then CNOT with q0 as control and q1 as target. The simulator must produce |Φ+⟩ = (|00⟩ + |11⟩)/√2.",
    gates: [
      { type: "H", qubit: 0 },
      { type: "CNOT", control: 0, target: 1 },
    ] as Gate[],
  },
  grover: {
    title: "Grover 2-qubit challenge",
    instructions:
      "Build a two-qubit Grover search circuit for the marked state |11⟩. A successful simulated state has all probability on |11⟩. You can load the guided circuit to inspect and run it.",
    gates: [
      { type: "H", qubit: 0 },
      { type: "H", qubit: 1 },
      { type: "H", qubit: 1 },
      { type: "CNOT", control: 0, target: 1 },
      { type: "H", qubit: 1 },
      { type: "H", qubit: 0 },
      { type: "H", qubit: 1 },
      { type: "X", qubit: 0 },
      { type: "X", qubit: 1 },
      { type: "H", qubit: 1 },
      { type: "CNOT", control: 0, target: 1 },
      { type: "H", qubit: 1 },
      { type: "X", qubit: 0 },
      { type: "X", qubit: 1 },
      { type: "H", qubit: 0 },
      { type: "H", qubit: 1 },
    ] as Gate[],
  },
} as const;

const GATE_NAMES: Record<string, string> = {
  H: "Hadamard",
  X: "Pauli X",
  Y: "Pauli Y",
  Z: "Pauli Z",
  CNOT: "Controlled NOT",
};
const GATE_STYLES: Record<string, string> = Object.fromEntries(
  PALETTE.map((gate) => [gate, "instrument-gate"]),
);

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
  const challengeKey = searchParams.get("challenge") as
    keyof typeof CHALLENGES | null;
  const challenge =
    challengeKey && Object.hasOwn(CHALLENGES, challengeKey)
      ? CHALLENGES[challengeKey]
      : undefined;
  const [numQubits, setNumQubits] = useState(2);
  const [shots, setShots] = useState(1024);
  const [gates, setGates] = useState<Gate[]>([]);
  const [selected, setSelected] = useState<PaletteGate | null>("H");
  const [cnotControl, setCnotControl] = useState<number | null>(null);
  const [cnotColumn, setCnotColumn] = useState<number | null>(null);
  const [result, setResult] = useState<CircuitResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultShots, setResultShots] = useState(1024);
  const [challengeStatus, setChallengeStatus] = useState<string | null>(null);
  const [executionStep, setExecutionStep] = useState(-1);
  const [placedColumn, setPlacedColumn] = useState<number | null>(null);
  const [dragMessage, setDragMessage] = useState("");
  const stageRef = useRef<HTMLElement>(null);
  const dragging = useGateDrag(loading, handleDrop);

  useEffect(() => {
    if (!loading || !gates.length) {
      setExecutionStep(-1);
      return;
    }
    setExecutionStep(0);
    const timer = window.setInterval(
      () => setExecutionStep((step) => Math.min(step + 1, gates.length - 1)),
      240,
    );
    return () => window.clearInterval(timer);
  }, [loading, gates.length]);
  useEffect(() => {
    if (placedColumn === null) return;
    const timer = window.setTimeout(() => setPlacedColumn(null), 220);
    return () => window.clearTimeout(timer);
  }, [placedColumn, gates]);

  function handleDrop(source: GateDragSource, target: GateDropTarget) {
    if (loading) return;
    if (source.type === "CNOT" && source.index === undefined) {
      setSelected("CNOT");
      setCnotControl(target.qubit);
      setCnotColumn(target.column);
      setDragMessage(
        `Control q${target.qubit} selected. Choose a different wire for the target.`,
      );
      return;
    }
    const next = dropGate(gates, source, target, numQubits);
    if (!next) {
      setDragMessage(
        "That move would put a linked qubit outside the circuit. The gate has not moved.",
      );
      return;
    }
    const column =
      source.index !== undefined && source.index < target.column
        ? target.column - 1
        : target.column;
    setGates(next);
    setResult(null);
    setError(null);
    setChallengeStatus(null);
    setCnotControl(null);
    setCnotColumn(null);
    setPlacedColumn(column);
    setDragMessage(
      `${source.type} ${source.index === undefined ? "placed" : "moved"} on q${target.qubit}, operation ${column + 1}.`,
    );
  }

  function moveByKeyboard(
    index: number,
    qubit: number,
    event: KeyboardEvent<HTMLButtonElement>,
  ) {
    if (
      !event.altKey ||
      !["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)
    )
      return;
    event.preventDefault();
    const column =
      event.key === "ArrowLeft"
        ? Math.max(0, index - 1)
        : event.key === "ArrowRight"
          ? Math.min(gates.length, index + 2)
          : index;
    const row =
      qubit +
      (event.key === "ArrowUp" ? -1 : event.key === "ArrowDown" ? 1 : 0);
    handleDrop(
      { type: gates[index].type, index, anchorQubit: qubit },
      { qubit: row, column },
    );
    const nextColumn = index < column ? column - 1 : column;
    window.requestAnimationFrame(() =>
      stageRef.current
        ?.querySelector<HTMLButtonElement>(
          `[data-circuit-qubit="${row}"][data-circuit-column="${nextColumn}"]`,
        )
        ?.focus(),
    );
  }

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
          (value): value is number => value !== undefined && value !== null,
        );
        return indices.every((index) => index < clamped);
      }),
    );
    setCnotControl(null);
    setCnotColumn(null);
    setResult(null);
    setChallengeStatus(null);
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
        setCnotColumn(null);
        return;
      }
      const column = cnotColumn ?? gates.length;
      setGates((current) => {
        const next = [...current];
        next.splice(column, 0, {
          type: "CNOT",
          control: cnotControl,
          target: qubit,
        });
        return next;
      });
      setPlacedColumn(column);
      setCnotControl(null);
      setCnotColumn(null);
      setResult(null);
      setChallengeStatus(null);
      return;
    }
    setGates((current) => [...current, { type: selected, qubit }]);
    setPlacedColumn(gates.length);
    setResult(null);
    setChallengeStatus(null);
  }

  function removeGate(index: number) {
    setGates((current) => current.filter((_, i) => i !== index));
    setResult(null);
    setChallengeStatus(null);
  }

  function clearCircuit() {
    setGates([]);
    setCnotControl(null);
    setCnotColumn(null);
    setResult(null);
    setChallengeStatus(null);
    setError(null);
  }

  function loadChallengeCircuit() {
    if (!challenge) return;
    setNumQubits(2);
    setGates(challenge.gates);
    setCnotControl(null);
    setCnotColumn(null);
    setError(null);
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
      setResultShots(shots);
      if (challengeKey === "bell") {
        const p00 = data.statevector ? probability(data.statevector[0]) : 0;
        const p11 = data.statevector ? probability(data.statevector[3]) : 0;
        const conceptualCircuit =
          gates.length === 2 &&
          gates[0].type === "H" &&
          gates[0].qubit === 0 &&
          gates[1].type === "CNOT" &&
          gates[1].control === 0 &&
          gates[1].target === 1;
        setChallengeStatus(
          conceptualCircuit &&
            Math.abs(p00 - 0.5) < 1e-9 &&
            Math.abs(p11 - 0.5) < 1e-9
            ? "Challenge complete: your required H → CNOT circuit simulated the Bell state |Φ+⟩."
            : "Not complete yet: use exactly H on q0 followed by CNOT control q0 → target q1, then simulate.",
        );
      } else if (challengeKey === "grover") {
        const p11 = data.statevector ? probability(data.statevector[3]) : 0;
        setChallengeStatus(
          numQubits === 2 && p11 > 0.999999
            ? "Challenge complete: simulation concentrates probability on the marked state |11⟩."
            : `Keep refining the circuit: the simulator reports P(|11⟩) = ${(p11 * 100).toFixed(1)}%.`,
        );
      }
    } catch (err) {
      setResult(null);
      setChallengeStatus(null);
      setError(err instanceof Error ? err.message : "Simulation failed");
    } finally {
      setLoading(false);
    }
  }

  const placementInstructions =
    selected === "CNOT"
      ? cnotControl === null
        ? "CNOT selected — click a qubit wire for the control, then the target."
        : `Control is q${cnotControl} — click a different qubit for the target.`
      : selected
        ? `${GATE_NAMES[selected]} selected — click a qubit wire to place it.`
        : "Select a gate, then click a qubit wire.";
  const editingInstructions =
    "Drag a gate onto a wire, or select it and click a wire. Drop before a gate to insert. Drag placed gates to move them; CNOT keeps its linked qubits together. For a new CNOT, choose the control first, then its target. Click a placed gate to remove it. With a gate focused, Alt + arrow keys move it. Escape cancels a drag. Gates run from left to right.";
  const interpretation = result
    ? `This run sampled ${resultShots} measurements. ${Object.entries(
        result.counts,
      )
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8)
        .map(
          ([bits, count]) =>
            `State |${bits}⟩ occurred ${count} times, or ${((100 * count) / resultShots).toFixed(1)} percent.`,
        )
        .join(
          " ",
        )} ${Object.keys(result.counts).length > 8 ? "The eight most frequent outcomes are summarized here; all counts are listed below." : ""} Measurement counts are samples and may vary between runs. Statevector probabilities are calculated from squared amplitude magnitudes, not from these sample counts.`
    : "";

  return (
    <div
      className="circuit-builder-system space-y-6"
      onClickCapture={dragging.suppressDragClick}
    >
      {dragging.drag && (
        <div
          className="gate-drag-preview instrument-gate"
          aria-hidden="true"
          style={{
            transform: `translate3d(${dragging.drag.x + 12}px, ${dragging.drag.y + 12}px, 0)`,
          }}
        >
          {dragging.drag.source.type}
        </div>
      )}
      <span role="status" className="sr-only">
        {dragMessage}
      </span>
      <fieldset disabled={loading} className="circuit-config">
        <legend className="sr-only">Circuit configuration</legend>
        {challenge && (
          <section
            id="circuit-challenge"
            className="panel p-6 circuit-challenge"
          >
            <h2 className="text-xl font-semibold">{challenge.title}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              {challenge.instructions}
            </p>
            <ListenButton
              className="mt-3"
              owner="circuit-challenge"
              label="Listen to challenge"
              segments={[
                {
                  id: "challenge",
                  title: challenge.title,
                  text: challenge.instructions,
                  targetId: "circuit-challenge",
                },
              ]}
            />
            <Button
              variant="secondary"
              onClick={loadChallengeCircuit}
              className="mt-4"
            >
              Load guided circuit
            </Button>
            {challengeStatus && (
              <ListenButton
                className="mt-3"
                owner="challenge-feedback"
                segments={[
                  {
                    id: "challenge-feedback",
                    title: "Challenge feedback",
                    text: challengeStatus,
                    targetId: "circuit-challenge",
                  },
                ]}
                label="Listen to feedback"
              />
            )}
            {challengeStatus && (
              <p
                role="status"
                className={`mt-4 rounded-lg p-3 text-sm ${challengeStatus.startsWith("Challenge complete") ? "bg-green-950/50 text-green-200" : "bg-amber-950/50 text-amber-200"}`}
              >
                {challengeStatus}
              </p>
            )}
          </section>
        )}
        <section className="panel instrument-toolbar">
          <div className="field">
            <span id="qubit-label">Qubits</span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="ui-button button-secondary !p-0 w-11"
                aria-label="Remove one qubit"
                disabled={numQubits <= 1}
                onClick={() => changeQubits(numQubits - 1)}
              >
                −
              </button>
              <span className="w-8 text-center text-lg font-semibold text-white">
                {numQubits}
              </span>
              <button
                type="button"
                className="ui-button button-secondary !p-0 w-11"
                aria-label="Add one qubit"
                disabled={numQubits >= 10}
                onClick={() => changeQubits(numQubits + 1)}
              >
                +
              </button>
            </div>
          </div>
          <label className="flex flex-col gap-2 text-sm text-slate-300">
            Shots
            <Input
              type="number"
              min={1}
              max={8192}
              value={shots}
              onChange={(event) =>
                setShots(
                  Math.min(8192, Math.max(1, Number(event.target.value) || 1)),
                )
              }
              className="w-28"
            />
          </label>
        </section>

        <section id="gate-instructions" className="panel p-6">
          <div className="flex justify-between gap-3 mb-5">
            <h2 className="section-title">Gate library</h2>
            <span className="technical">{gates.length} operations</span>
          </div>
          <div className="gate-palette">
            {PALETTE.map((gate) => (
              <button
                key={gate}
                {...dragging.bind({ type: gate })}
                aria-pressed={selected === gate}
                title={GATE_NAMES[gate]}
                type="button"
                onClick={() => {
                  setSelected((current) => (current === gate ? null : gate));
                  setCnotControl(null);
                  setCnotColumn(null);
                }}
                className={`draggable-gate rounded border px-4 py-3 font-mono text-sm font-semibold transition ${
                  GATE_STYLES[gate]
                } ${selected === gate ? "" : "hover:border-slate-300"}`}
              >
                {gate}
              </button>
            ))}
          </div>
          <p role="status" className="mt-4 text-sm text-slate-400 leading-6">
            {placementInstructions}
          </p>
          <p className="mt-2 text-xs text-slate-400">{editingInstructions}</p>
          <ListenButton
            className="mt-3"
            owner="gate-instructions"
            label="Listen to instructions"
            segments={[
              {
                id: "gates",
                title: "Circuit controls",
                text: `${placementInstructions} ${editingInstructions}`,
                targetId: "gate-instructions",
              },
            ]}
          />
        </section>

        <section
          ref={stageRef}
          className="circuit-stage"
          aria-label="Circuit canvas"
          aria-busy={loading}
        >
          <div
            className="grid items-center gap-x-2 gap-y-4"
            style={{
              gridTemplateColumns: `3rem repeat(${Math.max(gates.length, 1)}, 3.5rem) minmax(3rem, 1fr)`,
            }}
          >
            {Array.from({ length: numQubits }, (_, qubit) => (
              <QubitRow
                key={qubit}
                qubit={qubit}
                gates={gates}
                cnotControl={cnotControl}
                executionStep={executionStep}
                placedColumn={placedColumn}
                bindDrag={dragging.bind}
                onMoveKey={moveByKeyboard}
                onPlace={() => placeOnQubit(qubit)}
                onRemove={removeGate}
              />
            ))}
          </div>
        </section>
      </fieldset>
      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={onSimulate} disabled={loading}>
          {loading ? "Simulating…" : "Run simulation"}
        </Button>
        <Button variant="secondary" disabled={loading} onClick={clearCircuit}>
          Clear circuit
        </Button>
        <span role="status" className="technical">
          {loading
            ? "Executing circuit…"
            : result
              ? "Execution complete"
              : "Ready to simulate"}
        </span>
      </div>

      {error && <Status kind="error">{error}</Status>}
      {!result && !loading && !error && (
        <EmptyState
          title="Your results will appear here."
          description="Run the circuit to inspect measurement counts, amplitudes, and state probabilities. An empty circuit measures the initial all-zero state."
        />
      )}
      {result && (
        <section className="grid gap-6 lg:grid-cols-2">
          <div id="result-interpretation" className="panel p-5 lg:col-span-2">
            <div className="narration-section-heading">
              <h2 className="section-title">Understanding this result</h2>
              <ListenButton
                owner="result-interpretation"
                label="Listen to results"
                segments={[
                  {
                    id: "results",
                    title: "Understanding this result",
                    text: interpretation,
                    targetId: "result-interpretation",
                  },
                ]}
              />
            </div>
            <p className="text-sm text-slate-300 leading-7">{interpretation}</p>
          </div>
          <div className="panel p-5 min-w-0">
            <h2 className="section-title">Measurement counts</h2>
            <p className="technical mt-2">
              {resultShots.toLocaleString()} shots / bars relative to largest
              count
            </p>
            <ul className="result-list mt-4 space-y-3">
              {Object.entries(result.counts)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([bitstring, count]) => (
                  <li
                    key={bitstring}
                    className="flex items-center gap-3 text-sm"
                  >
                    <span className="shrink-0 font-mono text-xs sm:text-sm text-slate-300">
                      |{bitstring}⟩
                    </span>
                    <div className="h-3 flex-1 overflow-hidden rounded bg-surface-raised">
                      <div
                        className="h-full bg-quantum-500"
                        style={{ width: `${(count / maxCount) * 100}%` }}
                      />
                    </div>
                    <span className="w-24 shrink-0 text-right text-xs sm:text-sm text-slate-400">
                      {count} ({((count / resultShots) * 100).toFixed(1)}%)
                    </span>
                  </li>
                ))}
            </ul>
          </div>

          <div className="panel p-5 min-w-0">
            <h2 className="section-title">Statevector</h2>
            <p className="technical mt-2">Amplitude / probability</p>
            {result.statevector ? (
              <ul className="result-list mt-4 space-y-2 font-mono text-xs text-slate-300">
                {result.statevector.map((pair, index) => (
                  <li
                    key={index}
                    className="flex flex-wrap justify-between gap-x-4 gap-y-1 border-b border-white/5 py-1"
                  >
                    <span>|{index.toString(2).padStart(numQubits, "0")}⟩</span>
                    <span>
                      {formatAmplitude(pair)}{" "}
                      <span className="text-slate-400">
                        p={probability(pair).toFixed(3)}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-slate-400">
                No statevector returned.
              </p>
            )}
          </div>

          {result.circuit_diagram && (
            <div className="panel p-5 min-w-0 lg:col-span-2">
              <h2 className="text-lg font-semibold">Circuit diagram</h2>
              <pre className="mt-3 overflow-x-auto text-sm text-slate-300">
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
  executionStep,
  placedColumn,
  bindDrag,
  onMoveKey,
}: {
  qubit: number;
  gates: Gate[];
  cnotControl: number | null;
  onPlace: () => void;
  onRemove: (index: number) => void;
  executionStep: number;
  placedColumn: number | null;
  bindDrag: ReturnType<typeof useGateDrag>["bind"];
  onMoveKey: (
    index: number,
    qubit: number,
    event: KeyboardEvent<HTMLButtonElement>,
  ) => void;
}) {
  return (
    <>
      <button
        type="button"
        onClick={onPlace}
        data-circuit-qubit={qubit}
        data-circuit-column={gates.length}
        aria-label={`Place selected gate on qubit ${qubit}`}
        className={`w-14 rounded-md px-2 py-1 text-left font-mono text-sm ${
          cnotControl === qubit
            ? "bg-quantum-950 text-quantum-200"
            : "text-slate-400 hover:bg-surface-raised hover:text-white"
        }`}
      >
        q{qubit}
      </button>
      {(gates.length === 0 ? [null] : gates).map((gate, index) => {
        if (gate === null) {
          return (
            <button
              key="empty"
              data-circuit-qubit={qubit}
              data-circuit-column={0}
              type="button"
              onClick={onPlace}
              aria-label={`Place selected gate on qubit ${qubit}`}
              className="relative h-12 min-w-[3.5rem]"
            >
              <span className="absolute inset-x-0 top-1/2 h-px bg-slate-600" />
            </button>
          );
        }
        return (
          <GateCell
            key={`${index}-${gate.type}`}
            gate={gate}
            index={index}
            executing={executionStep === index}
            placed={placedColumn === index}
            bindDrag={bindDrag}
            onMoveKey={onMoveKey}
            qubit={qubit}
            onPlace={onPlace}
            onRemove={() => onRemove(index)}
          />
        );
      })}
      <button
        type="button"
        onClick={onPlace}
        data-circuit-qubit={qubit}
        data-circuit-column={gates.length}
        aria-label={`Place selected gate on qubit ${qubit}`}
        className="relative h-12 min-w-[2rem] flex-1"
      >
        <span className="absolute inset-x-0 top-1/2 h-px bg-slate-600" />
      </button>
    </>
  );
}

function GateCell({
  gate,
  qubit,
  onPlace,
  onRemove,
  index,
  executing,
  placed,
  bindDrag,
  onMoveKey,
}: {
  gate: Gate;
  qubit: number;
  onPlace: () => void;
  onRemove: () => void;
  index: number;
  executing: boolean;
  placed: boolean;
  bindDrag: ReturnType<typeof useGateDrag>["bind"];
  onMoveKey: (
    index: number,
    qubit: number,
    event: KeyboardEvent<HTMLButtonElement>,
  ) => void;
}) {
  const cell = {
    "data-circuit-qubit": qubit,
    "data-circuit-column": index,
    "data-executing": executing,
    "data-placed": placed,
  };
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
        {...cell}
        type="button"
        onClick={onPlace}
        aria-label={`Place selected gate on qubit ${qubit}`}
        className="circuit-cell relative flex h-12 min-w-[3.5rem] items-center justify-center"
      >
        <span className="absolute inset-x-0 top-1/2 h-px bg-slate-600" />
        {betweenCnot && (
          <span className="absolute -top-2 -bottom-2 w-px bg-quantum-300" />
        )}
      </button>
    );
  }

  if (isCnot) {
    const isControl = gate.control === qubit;
    return (
      <button
        {...cell}
        {...bindDrag({ type: gate.type, index, anchorQubit: qubit })}
        onKeyDown={(event) => onMoveKey(index, qubit, event)}
        type="button"
        onClick={onRemove}
        aria-label={`Remove CNOT, control q${gate.control}, target q${gate.target}`}
        title="Remove CNOT"
        className="circuit-cell draggable-gate relative flex h-12 min-w-[3.5rem] items-center justify-center"
      >
        <span className="absolute inset-x-0 top-1/2 h-px bg-slate-600" />
        <span
          className={`absolute w-px bg-quantum-300 ${qubit === Math.min(gate.control!, gate.target!) ? "top-1/2 -bottom-2" : "-top-2 bottom-1/2"}`}
        />
        {isControl ? (
          <span className="relative z-10 h-3 w-3 rounded-full bg-quantum-300" />
        ) : (
          <span className="relative z-10 flex h-6 w-6 items-center justify-center rounded-full border-2 border-quantum-300 text-xs text-quantum-200">
            ⊕
          </span>
        )}
      </button>
    );
  }

  return (
    <button
      {...cell}
      {...bindDrag({ type: gate.type, index, anchorQubit: qubit })}
      onKeyDown={(event) => onMoveKey(index, qubit, event)}
      type="button"
      onClick={onRemove}
      aria-label={`Remove ${gate.type} from qubit ${qubit}`}
      title={`Remove ${gate.type}`}
      className="circuit-cell draggable-gate relative flex h-12 min-w-[3.5rem] items-center justify-center"
    >
      <span className="absolute inset-x-0 top-1/2 h-px bg-slate-600" />
      <span
        className={`relative z-10 flex h-9 w-9 items-center justify-center rounded-md border font-mono text-sm font-bold ${
          GATE_STYLES[gate.type] ?? "bg-slate-600 border-gray-500"
        }`}
      >
        {gate.type}
      </span>
    </button>
  );
}
