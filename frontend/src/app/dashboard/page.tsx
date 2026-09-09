
"use client";

import { useEffect, useState } from "react";
import { API_URL } from "@/lib/api";

type Course = {
  name: string;
  progress: number;
};

type DashboardData = {
  user: {
    id: number;
    name: string;
    email: string;
  };
  courses: Course[];
  statistics: {
    quiz_score: number;
    challenges_completed: number;
    challenges_total: number;
    streak: number;
    xp: number;
  };
};

export default function DashboardPage() {
    const handleLogout = () => {
    localStorage.removeItem("access_token");
    window.location.href = "/login";
  };
  
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleLogout = () => {
  localStorage.removeItem("access_token");
  window.location.href = "/";
};
  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        // Get JWT token saved during login
        const token = localStorage.getItem("access_token");

        // If user is not logged in, send them to login page
        if (!token) {
          window.location.href = "/login";
          return;
        }

        // Fetch dashboard for the currently logged-in user
        const response = await fetch(
          `${API_URL}/api/dashboard/me`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        // Token is invalid or expired
        if (response.status === 401) {
          localStorage.removeItem("access_token");
          window.location.href = "/login";
          return;
        }

        // Other API errors
        if (!response.ok) {
          throw new Error("Failed to fetch dashboard data");
        }

        const data: DashboardData = await response.json();

        console.log("DASHBOARD API DATA:", data);

        setDashboard(data);
      } catch (err) {
        console.error(err);
        setError("Unable to load dashboard data.");
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  // Loading state
  if (loading) {
    return (
      <main className="min-h-screen bg-gray-950 p-8 text-white">
        <div className="mx-auto max-w-6xl">
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </main>
    );
  }

  // Error state
  if (error || !dashboard) {
    return (
      <main className="min-h-screen bg-gray-950 p-8 text-white">
        <div className="mx-auto max-w-6xl">
          <p className="text-red-400">
            {error || "Unable to load dashboard."}
          </p>
        </div>
      </main>
    );
  }

  const { user, courses, statistics } = dashboard;

  return (
    <main className="min-h-screen bg-gray-950 p-8 text-white">
      <div className="mx-auto max-w-6xl">
        {/* Dashboard Header */}
        <h1 className="text-3xl font-bold">My Dashboard</h1>
        <button
  onClick={handleLogout}
  className="mt-4 rounded-lg bg-red-600 px-4 py-2 font-semibold text-white hover:bg-red-700"
>
  Logout
</button>

        <p className="mt-2 text-gray-400">
          Welcome, {user.name}. Track your learning progress, scores, and
          achievements.
        </p>

        {/* Course Progress */}
        <section className="mt-8">
          <h2 className="text-xl font-semibold">Course Progress</h2>

          {courses.length === 0 ? (
            <div className="mt-4 rounded-xl border border-gray-800 bg-gray-900 p-5">
              <p className="text-gray-400">
                You are not enrolled in any courses yet.
              </p>
            </div>
          ) : (
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
          )}
        </section>

        {/* Learning Statistics */}
        <section className="mt-10">
          <h2 className="text-xl font-semibold">Learning Statistics</h2>

          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Quiz Score */}
            <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
              <p className="text-sm text-gray-400">Quiz Score</p>

              <p className="mt-2 text-3xl font-bold">
                {statistics.quiz_score}%
              </p>
            </div>

            {/* Challenges */}
            <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
              <p className="text-sm text-gray-400">Challenges</p>

              <p className="mt-2 text-3xl font-bold">
                {statistics.challenges_completed}/
                {statistics.challenges_total}
              </p>
            </div>

            {/* Learning Streak */}
            <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
              <p className="text-sm text-gray-400">Learning Streak</p>

              <p className="mt-2 text-3xl font-bold">
                {statistics.streak} days
              </p>
            </div>

            {/* XP */}
            <div className="rounded-xl border border-gray-800 bg-gray-900 p-5">
              <p className="text-sm text-gray-400">XP</p>

              <p className="mt-2 text-3xl font-bold">
                {statistics.xp}
              </p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

