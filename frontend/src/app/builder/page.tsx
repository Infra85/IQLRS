"use client";

import { useEffect, useState } from "react";
import CircuitBuilder from "@/components/circuit-builder/CircuitBuilder";
import { Suspense } from "react";

export default function BuilderPage() {
  const [loggedIn, setLoggedIn] = useState<boolean | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    setLoggedIn(!!token);
  }, []);

  // Check login status
  if (loggedIn === null) {
    return null;
  }

  // User is not logged in
  if (!loggedIn) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-950 p-8 text-white">
        <div className="w-full max-w-md rounded-2xl border border-gray-800 bg-gray-900 p-8 text-center shadow-xl">
          <h1 className="text-2xl font-bold">
            You are not logged in
          </h1>

          <p className="mt-3 text-gray-400">
            Please log in to access the Quantum Circuit Builder.
          </p>

          <button
            onClick={() => {
              window.location.href = "/login";
            }}
            className="mt-6 rounded-lg bg-quantum-600 px-6 py-3 font-medium text-white transition hover:bg-quantum-700"
          >
            Login
          </button>
        </div>
      </main>
    );
  }

  // User is logged in - show the Circuit Builder
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