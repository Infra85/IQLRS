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
  PALETTE,
  isLinked,
  isRotation,
  parseAngle,
  makeGate,
  validateCircuit,
  type PaletteGate,
  type GateDragSource,
  type GateDropTarget,
} from "./edit-circuit";
import { HardwareExecution } from "./HardwareExecution";
import { DebugControls } from "./DebugControls";
import { ExecutionTrace } from "./ExecutionTrace";
import { QuantumStateTable } from "./QuantumStateTable";
import { initialDebugSettings, makeDebugRequest } from "@/lib/simulation-trace";
import { ClassicalControls } from "./ClassicalControls";
import { ClassicalResults } from "./ClassicalResults";
import { withDefaultDestinations, validateClassicalCircuit, conditionLabel, referenceLabel } from "./classical-circuit";
import { useGateDrag } from "./use-gate-drag";
import { useSearchParams } from "next/navigation";
import { simulateCircuit, type CircuitResult, type Gate, type ClassicalRegister } from "@/lib/api";


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
  CNOT: "Controlled NOT (CX)",
  I: "Identity",
  S: "Phase pi/2",
  T: "Phase pi/4",
  RX: "X rotation", RY: "Y rotation", RZ: "Z rotation",
  CY: "Controlled Y", CZ: "Controlled Z", CH: "Controlled H",
  CRX: "Controlled X rotation", CRY: "Controlled Y rotation", CRZ: "Controlled Z rotation",
  SWAP: "Swap two qubits",
  MEASURE: "Measure one qubit", MEASURE_ALL: "Measure all qubits", RESET: "Reset to zero",
};
const GATE_STYLES: Record<string, string> = Object.fromEntries(
  PALETTE.map((gate) => [gate, "instrument-gate"]),
);

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
  const [executionMode, setExecutionMode] = useState("local");
  const [debugSettings, setDebugSettings] = useState(initialDebugSettings);
  const [inspectedOperation, setInspectedOperation] = useState<number | null>(null);
  const [numQubits, setNumQubits] = useState(2);
  const [registers, setRegisters] = useState<ClassicalRegister[] | undefined>(undefined);
  const [seedInput, setSeedInput] = useState("");
  const [recordShots, setRecordShots] = useState(false);
  const [recordLimit, setRecordLimit] = useState(20);
  const [shots, setShots] = useState(1024);
  const [gates, setGates] = useState<Gate[]>([]);
  const [selected, setSelected] = useState<PaletteGate | null>("H");
  const [thetaInput, setThetaInput] = useState("pi/2");
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

  function configuredGate(type: string, qubit: number, control?: number, theta?: number) {
    return withDefaultDestinations(makeGate(type, qubit, control, theta), registers, numQubits);
  }

  function updateRegisters(next: ClassicalRegister[] | undefined) {
    setRegisters(next);
    if (!registers && next) setGates(current => current.map(g => withDefaultDestinations(g, next, numQubits)));
    setResult(null);
    setError(null);
  }

  function renameRegister(index: number, name: string) {
    if (!registers) return;
    if (!/^[A-Za-z][A-Za-z0-9_]{0,31}$/.test(name) || registers.some((r, i) => i !== index && r.name === name)) {
      setError("Choose a unique register name beginning with a letter, using letters, digits or underscores.");
      return;
    }
    setError(null);
    const oldName = registers[index].name;
    setRegisters(registers.map((r, i) => i === index ? { ...r, name } : r));
    setGates(current => current.map(g => ({ ...g,
      ...(g.destinations ? { destinations: g.destinations.map(d => d.register === oldName ? { ...d, register: name } : d) } : {}),
      ...(g.condition?.register === oldName ? { condition: { ...g.condition, register: name } } : {}),
    })));
    setResult(null);
  }

  function updateOperation(index: number, gate: Gate) {
    setGates(current => current.map((g, i) => i === index ? gate : g));
    setResult(null);
    setChallengeStatus(null);
    setError(null);
  }

  function handleDrop(source: GateDragSource, target: GateDropTarget) {
    if (loading) return;
    if (isLinked(source.type) && source.index === undefined) {
      setSelected(source.type as PaletteGate);
      setCnotControl(target.qubit);
      setCnotColumn(target.column);
      setDragMessage(
        `Control q${target.qubit} selected. Choose a different wire for the target.`,
      );
      return;
    }
    let next: Gate[] | null;
    try {
      next = dropGate(gates, { ...source, theta: isRotation(source.type) && source.index === undefined ? parseAngle(thetaInput) : undefined }, target, numQubits);
    } catch (err) { setError((err as Error).message); return; }
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
    setGates(next.map(g => withDefaultDestinations(g, registers, numQubits)));
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
      }).map(g => g.type === "MEASURE_ALL" && g.destinations ? { ...g, destinations: g.destinations.slice(0, clamped) } : g),
    );
    setCnotControl(null);
    setCnotColumn(null);
    setResult(null);
    setChallengeStatus(null);
  }

  function placeOnQubit(qubit: number) {
    if (!selected) return;
    let theta = Math.PI / 2;
    try { if (isRotation(selected)) theta = parseAngle(thetaInput); }
    catch (err) { setError((err as Error).message); return; }
    setError(null);
    if (isLinked(selected)) {
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
        next.splice(column, 0, configuredGate(selected, qubit, cnotControl, theta));
        return next;
      });
      setPlacedColumn(column);
      setCnotControl(null);
      setCnotColumn(null);
      setResult(null);
      setChallengeStatus(null);
      return;
    }
    setGates((current) => [...current, configuredGate(selected, qubit, undefined, theta)]);
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
      validateCircuit(gates, numQubits);
      validateClassicalCircuit(gates, registers, numQubits);
      const seed = seedInput.trim() ? Number(seedInput) : undefined;
      if (seed !== undefined && (!Number.isSafeInteger(seed) || seed < 0)) throw new Error("Seed must be a non-negative safe integer, or blank for random runs.");
      if (recordShots && (!Number.isInteger(recordLimit) || recordLimit < 1 || recordLimit > 256)) throw new Error("Request between 1 and 256 shot records.");
      const data = await simulateCircuit({
        gates,
        num_qubits: numQubits,
        shots,
        backend: "qiskit",
        classical_registers: registers,
        seed,
        shot_record_limit: recordShots ? recordLimit : 0,
        debug: makeDebugRequest(debugSettings, shots, gates, numQubits),
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
    selected && isLinked(selected)
      ? cnotControl === null
        ? `${selected} selected — choose ${selected === "SWAP" ? "the first qubit, then the second" : "the control, then the target"}.`
        : `${selected === "SWAP" ? "First qubit" : "Control"} is q${cnotControl} — click a different qubit.`
      : selected
        ? `${GATE_NAMES[selected] ?? selected} selected — click a qubit wire to place it.`
        : "Select a gate, then click a qubit wire.";
  const editingInstructions =
    "Drag a gate onto a wire, or select it and click a wire. Drop before a gate to insert. Drag placed gates to move them; Linked gates keep their qubits together. For controlled gates, choose the control first, then its target. For SWAP, choose two distinct qubits. Click a placed gate to remove it. With a gate focused, Alt + arrow keys move it. Escape cancels a drag. Gates run from left to right.";
  const interpretation = result
    ? `This run sampled ${resultShots} measurements. ${Object.entries(
        result.counts,
      )
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8)
        .map(
          ([bits, count]) =>
            `${result.metadata?.counts_kind === "classical" ? `Classical result ${bits}` : `State |${bits}⟩`} occurred ${count} times, or ${((100 * count) / resultShots).toFixed(1)} percent.`,
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

        {executionMode === "local" && <section className="panel p-5 flex flex-wrap gap-4 items-end" aria-label="Shot execution options">
          <label className="text-sm">Random seed (optional)
            <Input aria-label="Random seed (optional)" value={seedInput} onChange={e => setSeedInput(e.target.value)} placeholder="Random each run" />
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={recordShots} onChange={e => setRecordShots(e.target.checked)} />
            Include shot history
          </label>
          {recordShots && <label className="text-sm">Shot records (maximum 256)
            <Input aria-label="Shot records" className="w-24" type="number" min={1} max={256} value={Number.isNaN(recordLimit) ? "" : recordLimit} onChange={e => setRecordLimit(e.target.valueAsNumber)} />
          </label>}
        </section>}

        {executionMode === "local" && <DebugControls settings={debugSettings} onChange={setDebugSettings} />}

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
                title={GATE_NAMES[gate] ?? gate}
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
          {selected && isRotation(selected) && (
            <label className="mt-4 flex flex-col gap-2 text-sm">Theta (radians)
              <Input aria-label="Theta (radians)" value={thetaInput} onChange={e => setThetaInput(e.target.value)} />
              <span>Examples: pi/2, -pi, 0.75. Applied when placing a gate.</span>
            </label>
          )}
          {gates.some(g => isRotation(g.type)) && <div className="mt-4 space-y-2">
            {gates.map((gate, index) => isRotation(gate.type) && <label key={index} className="flex items-center gap-3 text-sm">
              Operation {index + 1}: {gate.type} theta
              <Input aria-label={`Operation ${index + 1} theta`} key={`${index}-${gate.type}-${gate.params?.theta}`} defaultValue={String(gate.params?.theta)} onBlur={e => {
                try {
                  const theta = parseAngle(e.target.value);
                  setGates(current => current.map((g, i) => i === index ? { ...g, params: { theta } } : g));
                  setResult(null); setChallengeStatus(null); setError(null);
                } catch (err) { setError(`${(err as Error).message} Previous angle retained.`); e.target.value = String(gate.params?.theta); }
              }} />
            </label>)}
          </div>}
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

        <ClassicalControls registers={registers} gates={gates} numQubits={numQubits}
          onRegisters={updateRegisters} onRename={renameRegister} onGate={updateOperation} />

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
                executionStep={loading ? executionStep : executionMode === "local" && result?.debug ? inspectedOperation ?? -1 : -1}
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
      <HardwareExecution circuit={{ gates, num_qubits: numQubits, shots, classical_registers: registers }} mode={executionMode} onMode={setExecutionMode} />
      <div className="flex flex-wrap items-center gap-3">
        {executionMode === "local" && <Button onClick={onSimulate} disabled={loading}>
          {loading ? "Simulating…" : "Run simulation"}
        </Button>}
        <Button variant="secondary" disabled={loading} onClick={clearCircuit}>
          Clear circuit
        </Button>
        <span role="status" className="technical">
          {loading
            ? "Executing circuit…"
            : executionMode === "local" && result
              ? "Execution complete"
              : executionMode === "local" ? "Ready to simulate" : "Hardware execution selected"}
        </span>
      </div>

      {error && <Status kind="error">{error}</Status>}
      {executionMode === "local" && !result && !loading && !error && (
        <EmptyState
          title="Your results will appear here."
          description="Run the circuit to inspect measurement counts, amplitudes, and state probabilities. An empty circuit measures the initial all-zero state."
        />
      )}
      {executionMode === "local" && result && (
        <section className="grid gap-6 lg:grid-cols-2">
          <div id="result-interpretation" className="panel p-5 lg:col-span-2">
            <p className="text-sm text-slate-400 mb-4">{result.simulation_id ? "Saved to your account. View your activity in My progress." : "Guest simulation — sign in before running to save results and track progress."}</p>
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
              count · {result.metadata?.counts_kind === "classical" ? "final measured classical bits" : "final computational-basis sampling"}
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
                      {result.metadata?.counts_kind === "classical" ? bitstring : `|${bitstring}⟩`}
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
            <p className="technical mt-2">Amplitude / exact probability · q(n−1)…q0</p>
            {result.metadata?.statevector_scope === "last_shot" && <p className="mt-2 text-sm text-amber-200">Conditional state from the last shot, after measurement/reset. Counts aggregate all shots.</p>}
            {result.statevector ? (
              <QuantumStateTable label="Final quantum state" numQubits={numQubits} probabilities={result.statevector.map(probability)} statevector={result.statevector} />
            ) : (
              <p className="mt-3 text-sm text-slate-400">
                No statevector returned.
              </p>
            )}
          </div>

          {result.debug && <ExecutionTrace debug={result.debug} onOperation={setInspectedOperation} />}
          {(registers || !!result.shot_results?.length) && <ClassicalResults result={result} />}
          {!!result.measurements?.length && <div className="panel p-5 lg:col-span-2">
            <h2 className="section-title">Explicit measurements</h2>
            {result.measurements.map(m => <div key={m.operation} className="mt-3 text-sm">
              <p>Operation {m.operation + 1} · qubits {m.qubits.map(q => `q${q}`).join(", ")} · last shot: {m.bits}{m.destinations ? ` → ${m.destinations.map(referenceLabel).join(", ")}` : ""}</p>
              <p>Counts across shots: {Object.entries(result.measurement_counts?.[String(m.operation)] ?? {}).map(([bits, count]) => `${bits}: ${count}`).join(" · ")}</p>
            </div>)}
          </div>}
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
  const isCnot = isLinked(gate.type);
  const involved = isCnot
    ? gate.control === qubit || gate.target === qubit
    : gate.type === "MEASURE_ALL" || gate.qubit === qubit;

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
        aria-label={`Remove ${gate.type}, first q${gate.control}, target q${gate.target}`}
        title={`Remove ${gate.type}${gate.params ? `(${gate.params.theta})` : ""}`}
        className="circuit-cell draggable-gate relative flex h-12 min-w-[3.5rem] items-center justify-center"
      >
        {gate.condition && <span className="absolute -top-3 text-[9px] border-b border-dashed" title={conditionLabel(gate)} aria-label={conditionLabel(gate)}>IF</span>}
        <span className="absolute inset-x-0 top-1/2 h-px bg-slate-600" />
        <span
          className={`absolute w-px bg-quantum-300 ${qubit === Math.min(gate.control!, gate.target!) ? "top-1/2 -bottom-2" : "-top-2 bottom-1/2"}`}
        />
        {isControl && gate.type !== "SWAP" ? (
          <span className="relative z-10 h-3 w-3 rounded-full bg-quantum-300" />
        ) : (
          <span className="relative z-10 flex h-6 w-6 items-center justify-center rounded-full border-2 border-quantum-300 text-xs text-quantum-200">
            {gate.type === "SWAP" ? "×" : gate.type === "CNOT" ? "⊕" : gate.type.slice(1)}
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
      title={`Remove ${gate.type}${gate.params ? `(${gate.params.theta})` : ""}`}
      className="circuit-cell draggable-gate relative flex h-12 min-w-[3.5rem] items-center justify-center"
    >
      {gate.condition && <span className="absolute -top-3 text-[9px] border-b border-dashed" title={conditionLabel(gate)} aria-label={conditionLabel(gate)}>IF</span>}
      <span className="absolute inset-x-0 top-1/2 h-px bg-slate-600" />
      <span
        className={`relative z-10 flex h-9 w-9 items-center justify-center rounded-md border font-mono text-sm font-bold ${
          GATE_STYLES[gate.type] ?? "bg-slate-600 border-gray-500"
        }`}
      >
        {gate.type === "RESET" ? "|0⟩" : gate.type === "MEASURE_ALL" ? "M all" : gate.type === "MEASURE" ? "M" : gate.type}
      </span>
    </button>
  );
}
