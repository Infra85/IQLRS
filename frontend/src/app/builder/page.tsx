"use client";

import { useEffect, useState } from "react";
import CircuitBuilder from "@/components/circuit-builder/CircuitBuilder";
import { Suspense } from "react";

export default function BuilderPage() {
  const [loggedIn, setLoggedIn] = useState<boolean | null>(null);
  const [showLoginPopup, setShowLoginPopup] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    setLoggedIn(!!token);

    // Show recommendation popup only when user is not logged in
    if (!token) {
      setShowLoginPopup(true);
    }
  }, []);

  // Wait until login status is checked
  if (loggedIn === null) {
    return null;
  }

  return (
    <main className="builder-workbench min-h-screen p-8 text-white">

      {/* Login Recommendation Popup */}
      {showLoginPopup && !loggedIn && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="w-full max-w-md rounded-2xl border border-gray-800 bg-gray-900 p-8 text-center shadow-2xl">
            <h2 className="text-2xl font-bold">
              Login Recommended
            </h2>

            <p className="mt-4 text-gray-400">
              You are recommended to log in for a better experience
              and to access your dashboard.
            </p>

            <div className="mt-6 flex flex-col gap-3">

              {/* Login */}
              <button
                onClick={() => {
                  window.location.href = "/login";
                }}
                className="w-full rounded-lg bg-quantum-600 px-6 py-3 font-medium text-white transition hover:bg-quantum-700"
              >
                Login
              </button>

              {/* Continue without login */}
              <button
                onClick={() => {
                  setShowLoginPopup(false);
                }}
                className="w-full rounded-lg border border-gray-700 px-6 py-3 font-medium text-gray-300 transition hover:bg-gray-800 hover:text-white"
              >
                Continue without login
              </button>

            </div>
          </div>
        </div>
      )}

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

      <p className="system-label mt-12"><span />SIMULATOR / LIVE INSTRUMENT</p>
      <h1 className="builder-title mt-4 text-3xl font-bold">
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
