"use client";

import { useEffect, useState } from "react";
import { QuantumLandingScene } from "@/components/quantum-landing-scene";

export default function Home() {
  const [loggedIn, setLoggedIn] = useState(false);
  useEffect(() => setLoggedIn(Boolean(localStorage.getItem("access_token"))), []);

  return (
    <main className="homepage">
      <div className="home-account-control">{loggedIn ? <a href="/dashboard">ACCOUNT / DASHBOARD</a> : <a href="/login">LOGIN / REGISTER</a>}</div>
      <QuantumLandingScene />
      <section className="landing-quiet-section">
        <p className="system-label"><span />IQLRS / LEARNING ENVIRONMENT</p>
        <div><h2>FROM FIRST<br />PRINCIPLES TO<br /><em>REAL CIRCUITS.</em></h2></div>
        <p className="quiet-description">The learning path preserves the details that make quantum computing rigorous: states, amplitudes, measurements, algorithms, and practical circuit experiments.</p>
        <div className="landing-links"><a href="/learn">Browse modules <b>→</b></a><a href="/editor">Use the code lab <b>→</b></a><a href="/dashboard">Track progress <b>→</b></a></div>
      </section>
    </main>
  );
}
