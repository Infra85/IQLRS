"use client";
import { ListenButton } from "@/components/narration/provider";
import { useState } from "react";
import { PageHeader, Status } from "@/components/ui/page";
import { Button } from "@/components/ui/button";
import { FormField, Select } from "@/components/ui/input";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import Link from "next/link";
const examples = {
  qiskit: `from qiskit import QuantumCircuit\n\n# Prepare a Bell state\ncircuit = QuantumCircuit(2)\ncircuit.h(0)\ncircuit.cx(0, 1)\n\nprint(circuit.draw())\n`,
  pennylane: `import pennylane as qml\n\ndevice = qml.device("default.qubit", wires=2)\n\n@qml.qnode(device)\ndef bell_state():\n    qml.Hadamard(wires=0)\n    qml.CNOT(wires=[0, 1])\n    return qml.probs(wires=[0, 1])\n\nprint(bell_state())\n`,
  cirq: `import cirq\n\nq0, q1 = cirq.LineQubit.range(2)\ncircuit = cirq.Circuit(\n    cirq.H(q0),\n    cirq.CNOT(q0, q1),\n)\n\nprint(circuit)\n`,
};
const steps = [
  "Initialize two qubits in |00⟩.",
  "Apply H to the first qubit.",
  "Apply CNOT from the first qubit to the second.",
];
type Framework = keyof typeof examples;
const introduction =
  "Explore a Bell-state example, edit the Python, and download your experiment. Each framework has its own editable draft.";
export default function EditorPage() {
  const [framework, setFramework] = useState<Framework>("qiskit");
  const [drafts, setDrafts] = useState(examples);
  const [notice, setNotice] = useState<string | null>(null);
  function download() {
    const url = URL.createObjectURL(
      new Blob([drafts[framework]], { type: "text/x-python" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = `${framework}-circuit.py`;
    a.click();
    URL.revokeObjectURL(url);
    setNotice(
      "Python file downloaded. Run it in your local environment with the selected framework installed.",
    );
  }
  return (
    <main className="page">
      <PageHeader
        eyebrow="LAB / 02 — CODE NOTEBOOK"
        title="Express it in code."
        description={introduction}
      />
      <div className="mb-6">
        <ListenButton
          owner="page-introduction"
          segments={[
            {
              id: "introduction",
              title: "Express it in code.",
              text: introduction,
            },
          ]}
          label="Listen to introduction"
        />
      </div>
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <Card>
          <CardHeader>
            <h2 className="section-title">Experiment notebook</h2>
            <span className="technical">Python</span>
          </CardHeader>
          <CardContent>
            <div className="max-w-xs mb-5">
              <FormField label="Framework" id="framework">
                <Select
                  id="framework"
                  value={framework}
                  onChange={(e) => {
                    setFramework(e.target.value as Framework);
                    setNotice(null);
                  }}
                >
                  <option value="qiskit">Qiskit</option>
                  <option value="pennylane">PennyLane</option>
                  <option value="cirq">Cirq</option>
                </Select>
              </FormField>
            </div>
            <label className="sr-only" htmlFor="code">
              Python source code
            </label>
            <textarea
              id="code"
              spellCheck={false}
              className="ui-input code-area"
              value={drafts[framework]}
              onChange={(e) =>
                setDrafts({ ...drafts, [framework]: e.target.value })
              }
            />
            <div className="mt-5 flex flex-wrap gap-3">
              <Button onClick={download}>Download .py ↓</Button>
              <Button
                variant="secondary"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(drafts[framework]);
                    setNotice("Code copied to clipboard.");
                  } catch {
                    setNotice(
                      "Clipboard unavailable. Select the code and copy it manually.",
                    );
                  }
                }}
              >
                Copy code
              </Button>
            </div>
            <p className="mt-3 text-xs text-slate-400">
              Drafts are kept while this page is open. Download to keep your
              changes.
            </p>
            {notice && (
              <div className="mt-5">
                <Status>{notice}</Status>
              </div>
            )}
          </CardContent>
        </Card>
        <aside className="space-y-6">
          <Status>
            Server-side code execution is not available yet. Download your code
            to run locally, or use the circuit builder for live simulation.
          </Status>
          <div id="code-explanation" className="panel p-6">
            <p className="technical mb-4">Experiment / 01</p>
            <h2 className="section-title">From two qubits to a Bell state.</h2>
            <ol className="list-decimal pl-5 my-5 space-y-3 text-sm leading-7 text-slate-400">
              {steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
            <ListenButton
              className="mb-3"
              owner="code-explanation"
              label="Listen to explanation"
              segments={[
                {
                  id: "bell-code",
                  title: "From two qubits to a Bell state",
                  text: steps.join("\n"),
                  targetId: "code-explanation",
                },
              ]}
            />
            <Button asChild variant="secondary">
              <Link href="/builder?challenge=bell">
                Simulate this circuit ↗
              </Link>
            </Button>
          </div>
        </aside>
      </div>
    </main>
  );
}
