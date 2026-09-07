import Link from "next/link";

export default function Home() {
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center bg-gray-950 text-white">
      <Link
    href="/login"
    className="absolute right-6 top-6 rounded-lg border border-gray-700 px-5 py-2.5 font-medium transition hover:bg-gray-800"
  >
    Login
      </Link>
      <h1 className="text-5xl font-bold tracking-tight">
        Quantum<span className="text-quantum-500">Learn</span>
      </h1>
      <p className="mt-4 text-lg text-gray-400">
        AI-Based Interactive Quantum Algorithm Learning Platform
      </p>
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
