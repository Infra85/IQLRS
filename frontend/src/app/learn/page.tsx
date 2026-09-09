"use client";

import { useEffect, useState } from "react";
import { modules } from "./modules";
import ModuleItem from "./components/ModuleItem";

export default function LearnPage() {
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
    <main className="min-h-screen bg-gray-950 p-8 text-white">
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

      {/* Learning Modules */}
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