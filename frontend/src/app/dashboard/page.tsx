"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  PageHeader,
  LoadingState,
  Status,
  EmptyState,
} from "@/components/ui/page";
import { Card, CardContent } from "@/components/ui/card";
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
        const response = await fetch(`${API_URL}/api/dashboard/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

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

  if (loading)
    return (
      <main className="page">
        <LoadingState label="Loading your learning progress…" />
      </main>
    );
  if (error || !dashboard)
    return (
      <main className="page">
        <PageHeader
          eyebrow="ACCOUNT / PROGRESS"
          title="Your learning dashboard."
        />
        <Status kind="error">{error || "Unable to load dashboard."}</Status>
        <Button
          className="mt-5"
          variant="secondary"
          onClick={() => window.location.reload()}
        >
          Try again
        </Button>
      </main>
    );
  const { user, courses, statistics } = dashboard;
  const stats = [
    { label: "Quiz score", value: `${statistics.quiz_score}%` },
    {
      label: "Challenges",
      value: `${statistics.challenges_completed} / ${statistics.challenges_total}`,
    },
    { label: "Learning streak", value: `${statistics.streak} days` },
    { label: "Experience points", value: statistics.xp.toLocaleString() },
  ];
  return (
    <main className="page">
      <PageHeader
        eyebrow="ACCOUNT / LEARNING RECORD"
        title={`Welcome back, ${user.name}.`}
        description="Every concept understood. Every circuit explored. Your learning, in perspective."
        action={
          <Button variant="secondary" onClick={handleLogout}>
            Sign out
          </Button>
        }
      />
      <section className="stat-grid" aria-label="Learning statistics">
        {stats.map((stat) => (
          <div className="stat" key={stat.label}>
            <p className="technical">{stat.label}</p>
            <p className="stat-value">{stat.value}</p>
          </div>
        ))}
      </section>
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_18rem]">
        <section>
          <div className="flex items-center justify-between mb-5 gap-4">
            <h2 className="section-title">Your course progress</h2>
            <Link
              className="text-sm text-slate-300 hover:text-white"
              href="/learn"
            >
              View curriculum ↗
            </Link>
          </div>
          {courses.length === 0 ? (
            <EmptyState
              title="Your learning path starts here."
              description="Explore the curriculum and begin with the foundations of quantum states."
              href="/learn"
            />
          ) : (
            <div className="space-y-4">
              {courses.map((course) => (
                <Card key={course.name}>
                  <CardContent>
                    <div className="flex justify-between gap-5 mb-4">
                      <h3>{course.name}</h3>
                      <span className="font-mono text-sm text-quantum-300">
                        {course.progress}%
                      </span>
                    </div>
                    <progress
                      className="progress-track"
                      value={course.progress}
                      max={100}
                      aria-label={`${course.name} progress`}
                    />
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </section>
        <aside className="space-y-6">
          <Card>
            <CardContent>
              <p className="technical mb-4">Your account</p>
              <p className="font-medium">{user.name}</p>
              <p className="mt-2 text-sm text-slate-400 break-all">
                {user.email}
              </p>
            </CardContent>
          </Card>
          <div className="border-t pt-6">
            <p className="technical mb-4">Theory → practice</p>
            <h2 className="section-title mb-3">Make your next discovery.</h2>
            <p className="text-sm text-slate-400 leading-7 mb-5">
              Turn what you’ve learned into a circuit. Start with a qubit and
              see where it takes you.
            </p>
            <Button asChild variant="secondary">
              <Link href="/builder">Open circuit builder ↗</Link>
            </Button>
          </div>
        </aside>
      </div>
    </main>
  );
}
