import CircuitBuilder from "@/components/circuit-builder/CircuitBuilder";
import { Suspense } from "react";

export default function BuilderPage() {
  return (
    <main className="min-h-screen bg-gray-950 p-8 text-white">

      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        
        {/* Home Button - Top Left */}
        <a
          href="/"
          className="flex h-10 w-10 items-center justify-center rounded-full border border-gray-700 bg-gray-900 text-gray-300 transition hover:bg-gray-800 hover:text-white"
          title="Home"
          aria-label="Home"
        >
          🏠
        </a>

        {/* Dashboard Button - Top Right */}
        <a
          href="/dashboard"
          className="flex h-10 w-10 items-center justify-center rounded-full border border-gray-700 bg-gray-900 text-gray-300 transition hover:bg-gray-800 hover:text-white"
          title="Dashboard"
          aria-label="Dashboard"
        >
          📊
        </a>

      </div>

      <h1 className="mt-4 text-3xl font-bold">
        Quantum Circuit Builder
      </h1>

      <p className="mt-2 text-gray-400">
        Place gates on qubit wires, then simulate. Supported gates: H, X, Y, Z, CNOT.
      </p>

      <Suspense
        fallback={
          <p className="mt-8 text-gray-400">
            Loading circuit builder…
          </p>
        }
      >
        <CircuitBuilder />
      </Suspense>

    </main>
  );
}