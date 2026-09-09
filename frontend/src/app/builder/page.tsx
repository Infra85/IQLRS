import Link from "next/link";

export default function BuilderPage() {
  return (
    <main className="min-h-screen bg-gray-950 p-8 text-white">
      
      {/* Top bar */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Quantum Circuit Builder</h1>
          <p className="mt-2 text-gray-400">
            Drag and drop quantum gates to build circuits.
          </p>
        </div>

        {/* Dashboard Button */}
        <Link
          href="/dashboard"
          className="rounded-lg bg-blue-600 px-5 py-2.5 font-semibold text-white transition hover:bg-blue-700"
        >
          Dashboard
        </Link>
      </div>

    </main>
  );
}