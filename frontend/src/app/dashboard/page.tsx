"use client";
export default function DashboardPage() {
  const courses = [
    { name: "Quantum Fundamentals", progress: 80 },
    { name: "Quantum Gates", progress: 60 },
    { name: "Entanglement", progress: 40 },
    { name: "Algorithms", progress: 20 },
  ];

  const handleLogout = () => {
  window.location.href = "/";
};

  return (
    <main className="min-h-screen bg-gray-950 p-8 text-white">
      <div className="mx-auto max-w-6xl">
        <h1 className="text-3xl font-bold">My Dashboard</h1>
        <button
  onClick={handleLogout}
  className="mt-4 rounded-lg bg-red-600 px-4 py-2 font-semibold text-white hover:bg-red-700"
>
  Logout
</button>

        <p className="mt-2 text-gray-400">
          Track your learning progress, scores, and achievements.
        </p>

        <section className="mt-8">
          <h2 className="text-xl font-semibold">Course Progress</h2>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            {courses.map((course) => (
              <div
                key={course.name}
                className="rounded-xl border border-gray-800 bg-gray-900 p-5"
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">{course.name}</h3>

                  <span className="text-sm text-gray-400">
                    {course.progress}%
                  </span>
                </div>

                <div className="mt-3 h-3 w-full rounded-full bg-gray-800">
                  <div
                    className="h-3 rounded-full bg-blue-500"
                    style={{ width: `${course.progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-10">
          <h2 className="text-xl font-semibold">Learning Statistics</h2>

          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
              <p className="text-sm text-gray-400">Quiz Score</p>
              <p className="mt-2 text-3xl font-bold">82%</p>
            </div>

            <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
              <p className="text-sm text-gray-400">Challenges</p>
              <p className="mt-2 text-3xl font-bold">12/20</p>
            </div>

            <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
              <p className="text-sm text-gray-400">Learning Streak</p>
              <p className="mt-2 text-3xl font-bold">7 days</p>
            </div>

            <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
              <p className="text-sm text-gray-400">XP</p>
              <p className="mt-2 text-3xl font-bold">1250</p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}