"use client";

import { useEffect, useRef } from "react";

/** A conceptual state-field illustration, not a literal quantum simulation. */
export function QuantumLandingScene() {
  const sceneRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return;
    let frame = 0;
    const update = () => {
      frame = 0;
      const rect = scene.getBoundingClientRect();
      const progress = Math.min(1, Math.max(0, -rect.top / Math.max(rect.height - window.innerHeight, 1)));
      scene.style.setProperty("--scene-progress", progress.toFixed(3));
    };
    const onScroll = () => { if (!frame) frame = window.requestAnimationFrame(update); };
    const onPointerMove = (event: PointerEvent) => {
      const rect = scene.getBoundingClientRect();
      scene.style.setProperty("--pointer-x", ((event.clientX - rect.left) / rect.width - .5).toFixed(3));
      scene.style.setProperty("--pointer-y", ((event.clientY - rect.top) / rect.height - .5).toFixed(3));
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", update);
    scene.addEventListener("pointermove", onPointerMove);
    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", update);
      scene.removeEventListener("pointermove", onPointerMove);
    };
  }, []);

  return (
    <div ref={sceneRef} className="quantum-story" style={{ "--scene-progress": 0, "--pointer-x": 0, "--pointer-y": 0 } as React.CSSProperties}>
      <section className="quantum-hero-scene">
        <div className="scene-copy">
          <p className="system-label"><span />SYSTEM / QUANTUM-03</p>
          <h1>LEARN<br /><em>QUANTUM</em><br />VISUALLY.</h1>
          <p className="scene-intro">Build an intuition for quantum states, transformations, and measurement through lessons you can see, test, and run.</p>
          <div className="scene-actions"><a className="chrome-action" href="/learn">Enter learning path <b>↗</b></a><a className="quiet-action" href="/builder">Open circuit instrument</a></div>
          <p className="scroll-index"><i /> SCROLL / OBSERVE THE STATE</p>
        </div>
        <div className="scene-object" aria-label="Conceptual visualization of a quantum state transforming into a probability field">
          <div className="orbit orbit-one" /><div className="orbit orbit-two" />
          <div className="chrome-qubit"><span className="qubit-core" /><span className="qubit-axis" /></div>
          <div className="scene-metadata metadata-left">QUBIT / 01<br /><b>|ψ⟩</b></div><div className="scene-metadata metadata-right">STATE / COHERENT<br /><b>α|0⟩ + β|1⟩</b></div>
          <div className="probability-field" aria-hidden="true">{Array.from({ length: 72 }, (_, index) => <i key={index} style={{ "--i": index } as React.CSSProperties} />)}</div>
        </div>
      </section>
      <section className="state-scene"><div className="state-visual" aria-hidden="true"><div className="wave wave-a" /><div className="wave wave-b" /><div className="field-label">P(0) 0.50<br />P(1) 0.50</div></div><div className="state-copy"><p className="system-label"><span />01 / STATE SPACE</p><h2>ONE QUBIT.<br />MANY <em>OUTCOMES.</em></h2><p>A superposition is represented here as a conceptual probability field. It describes possible measurement outcomes—not a tiny object physically split in two.</p><a href="/learn/2" className="text-action">Explore superposition <b>→</b></a></div></section>
      <section className="circuit-scene"><div className="circuit-copy"><p className="system-label"><span />02 / TRANSFORM</p><h2>OPERATIONS<br />SHAPE THE <em>FIELD.</em></h2><p>Quantum gates change amplitudes. Follow a readable circuit, then run your own version in the simulator.</p><a href="/builder" className="chrome-action">Build a circuit <b>↗</b></a></div><div className="concept-circuit" aria-label="Conceptual quantum circuit showing a Hadamard gate followed by a controlled not gate"><span className="circuit-name">CONCEPTUAL CIRCUIT / BELL STATE</span><div className="c-wire"><i>q0</i><b className="gate">H</b><b className="control" /><b className="target">⊕</b></div><div className="c-wire"><i>q1</i><b className="empty-gate" /><b className="link" /><b className="target ghost">⊕</b></div><span className="circuit-note">H → CNOT makes correlations observable.</span></div></section>
    </div>
  );
}
