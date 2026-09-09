"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { modules } from "./modules";
import ModuleItem from "./components/ModuleItem";

export default function LearnPage() {
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
            Please log in to access the learning modules.
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

  // User is logged in - show existing learning modules
  return (
    <main className="min-h-screen bg-gray-950 p-8 text-white">
      <h1 className="mb-6 text-3xl font-bold">
        Quantum Computing Learning Path
      </h1>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {modules.map((module) => (
          <ModuleItem key={module.id} module={module} />
        ))}
      </div>
    </main>
  );
}