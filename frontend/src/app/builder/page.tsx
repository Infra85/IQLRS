import CircuitBuilder from "@/components/circuit-builder/CircuitBuilder";
import { Suspense } from "react";

export default function BuilderPage() {
  return (
    <main className="min-h-screen bg-gray-950 p-8 text-white">
      <a href="/" className="text-sm text-gray-500 transition hover:text-gray-300">
        ← Home
      </a>
      <h1 className="mt-4 text-3xl font-bold">Quantum Circuit Builder</h1>
      <p className="mt-2 text-gray-400">
        Place gates on qubit wires, then simulate. Supported gates: H, X, Y, Z, CNOT.
      </p>
      <Suspense fallback={<p className="mt-8 text-gray-400">Loading circuit builder…</p>}>
        <CircuitBuilder />
      </Suspense>
    </main>
  );
}
