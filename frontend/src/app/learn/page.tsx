"use client";

import { useEffect, useState } from "react";
import { modules } from "./modules";
import ModuleItem from "./components/ModuleItem";

export default function LearnPage() {
  const [loggedIn, setLoggedIn] = useState<boolean | null>(null);
  const [showLoginPopup, setShowLoginPopup] = useState(false);
  useEffect(() => { const token = localStorage.getItem("access_token"); setLoggedIn(Boolean(token)); setShowLoginPopup(!token); }, []);
  if (loggedIn === null) return null;
  return <main className="learning-page">
    {showLoginPopup && <div className="learning-modal"><div className="learning-modal-card"><p className="system-label"><span />ACCOUNT OPTIONAL</p><h2>KEEP YOUR<br />PROGRESS.</h2><p>Sign in to save your learning path and bring circuit experiments into your dashboard.</p><a className="chrome-action" href="/login">Sign in <b>↗</b></a><button onClick={() => setShowLoginPopup(false)}>Continue as guest</button></div></div>}
    <header className="learning-header"><p className="system-label"><span />CURRICULUM / 08 MODULES</p><h1>THE QUANTUM<br /><em>LEARNING PATH.</em></h1><p>Start with states and measurement, then use circuits to make the ideas operational.</p></header>
    <section className="module-index">{modules.map((module, index) => <ModuleItem key={module.id} module={module} index={index} />)}</section>
  </main>;
}
