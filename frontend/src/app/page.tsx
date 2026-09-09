"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export default function Home() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [showLogout, setShowLogout] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    setLoggedIn(!!token);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    window.location.href = "/";
  };

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center bg-gray-950 text-white">
      {/* Login / User Menu */}
      {loggedIn ? (
        <div className="absolute right-6 top-6">
          <button
            onClick={() => setShowLogout(!showLogout)}
            className="h-10 w-10 rounded-full border border-gray-700 bg-black transition hover:border-gray-500"
            aria-label="Account menu"
          />

          {showLogout && (
            <div className="absolute right-0 mt-2 rounded-lg border border-gray-700 bg-gray-900 p-2 shadow-lg">
              <button
                onClick={handleLogout}
                className="rounded-md px-4 py-2 text-sm text-white transition hover:bg-gray-800"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      ) : (
        <Link
          href="/login"
          className="absolute right-6 top-6 rounded-lg border border-quantum-600 px-5 py-2.5 font-medium transition hover:bg-quantum-700"
        >
          Login/Register
        </Link>
      )}

      {/* Main Content */}
      <h1 className="text-5xl font-bold tracking-tight">
        IQ<span className="text-quantum-500">LRS</span>
      </h1>

      <p className="mt-4 text-lg text-gray-400">
        Intelligent Quantum Learning And Research System,
        <br />
        AI-Based Interactive Quantum Algorithm Learning Platform
      </p>

      {/* Main Buttons */}
      <div className="mt-10 flex gap-4">
        <a
          href="/learn"
          className="rounded-lg bg-quantum-600 px-6 py-3 font-medium transition hover:bg-quantum-700"
        >
          Start Learning
        </a>

        <a
          href="/builder"
          className="rounded-lg border border-gray-700 px-6 py-3 font-medium transition hover:bg-gray-800"
        >
          Circuit Builder
        </a>
      </div>
    </main>
  );
}
