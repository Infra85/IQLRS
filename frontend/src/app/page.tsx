"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { QuantumLandingScene } from "@/components/quantum-landing-scene";

export default function Home() {
  const [loggedIn, setLoggedIn] = useState(false);
  useEffect(
    () => setLoggedIn(Boolean(localStorage.getItem("access_token"))),
    [],
  );

  return (
    <main className="homepage">
      <div className="home-account-control">
        {loggedIn ? (
          <Link href="/dashboard">ACCOUNT / DASHBOARD</Link>
        ) : (
          <Link href="/login">LOGIN / REGISTER</Link>
        )}
      </div>
      <QuantumLandingScene />
      <section className="landing-quiet-section">
        <p className="system-label">
          <span />
          IQLRS / LEARNING ENVIRONMENT
        </p>
        <div>
          <h2>
            FROM FIRST
            <br />
            PRINCIPLES TO
            <br />
            <em>REAL CIRCUITS.</em>
          </h2>
        </div>
        <p className="quiet-description">
          The learning path preserves the details that make quantum computing
          rigorous: states, amplitudes, measurements, algorithms, and practical
          circuit experiments.
        </p>
        <div className="landing-links">
          <Link href="/learn">
            Browse modules <b>→</b>
          </Link>
          <Link href="/editor">
            Use the code lab <b>→</b>
          </Link>
          <Link href="/dashboard">
            Track progress <b>→</b>
          </Link>
        </div>
      </section>
    </main>
  );
}
