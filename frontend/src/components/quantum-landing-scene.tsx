"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { ListenButton } from "./narration/provider";

const stateExplanation =
  "A superposition is represented here as a conceptual probability field. It describes possible measurement outcomes—not a tiny object physically split in two.";
const circuitExplanation =
  "Quantum gates change amplitudes. Follow a readable circuit, then run your own version in the simulator.";

/** A conceptual state-field illustration, not a literal quantum simulation. */
export function QuantumLandingScene() {
  const sceneRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return;
    let frame = 0;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    const observer = new IntersectionObserver(
      ([entry]) => {
        scene.dataset.visible = String(entry.isIntersecting);
      },
      { rootMargin: "100px" },
    );
    observer.observe(scene);

    const update = () => {
      frame = 0;
      if (reduced.matches) return;
      const rect = scene.getBoundingClientRect();
      const progress = Math.min(
        1,
        Math.max(0, -rect.top / Math.max(rect.height - window.innerHeight, 1)),
      );
      scene.style.setProperty("--scene-progress", progress.toFixed(3));
    };
    const onScroll = () => {
      if (!frame) frame = window.requestAnimationFrame(update);
    };
    const onPointerMove = (event: PointerEvent) => {
      if (reduced.matches) return;
      const rect = scene.getBoundingClientRect();
      scene.style.setProperty(
        "--pointer-x",
        ((event.clientX - rect.left) / rect.width - 0.5).toFixed(3),
      );
      scene.style.setProperty(
        "--pointer-y",
        ((event.clientY - rect.top) / rect.height - 0.5).toFixed(3),
      );
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", update);
    scene.addEventListener("pointermove", onPointerMove);
    return () => {
      observer.disconnect();
      window.cancelAnimationFrame(frame);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", update);
      scene.removeEventListener("pointermove", onPointerMove);
    };
  }, []);

  return (
    <div
      ref={sceneRef}
      className="quantum-story"
      style={
        {
          "--scene-progress": 0,
          "--pointer-x": 0,
          "--pointer-y": 0,
        } as React.CSSProperties
      }
    >
      <section className="quantum-hero-scene">
        <div className="scene-copy">
          <p className="system-label">
            <span />
            SYSTEM / QUANTUM-03
          </p>
          <h1>
            LEARN
            <br />
            <em>QUANTUM</em>
            <br />
            VISUALLY.
          </h1>
          <p className="scene-intro">
            Build an intuition for quantum states, transformations, and
            measurement through lessons you can see, test, and run.
          </p>
          <div className="scene-actions">
            <Link className="chrome-action" href="/learn">
              Enter learning path <b>↗</b>
            </Link>
            <Link className="quiet-action" href="/builder">
              Open circuit instrument
            </Link>
          </div>
          <p className="scroll-index">
            <i /> SCROLL / OBSERVE THE STATE
          </p>
        </div>
        <div
          className="scene-object"
          role="img"
          aria-label="Conceptual visualization of a quantum state transforming into a probability field"
        >
          <div className="hardware-ring hardware-ring-one" />
          <div className="hardware-ring hardware-ring-two" />
          <div className="chrome-qubit">
            <span className="qubit-core" />
            <span className="qubit-axis" />
          </div>
          <div className="scene-metadata metadata-left">
            QUBIT / 01
            <br />
            <b>|ψ⟩</b>
          </div>
          <div className="scene-metadata metadata-right">
            STATE / COHERENT
            <br />
            <b>α|0⟩ + β|1⟩</b>
          </div>
          <div className="probability-field" aria-hidden="true">
            {Array.from({ length: 72 }, (_, index) => (
              <i
                key={index}
                style={
                  {
                    "--left": `${8 + ((index * 37) % 84)}%`,
                    "--top": `${8 + ((index * 61) % 84)}%`,
                    "--size": `${1 + (index % 4) * 0.6}px`,
                    "--alpha": 0.2 + (index % 6) * 0.12,
                  } as React.CSSProperties
                }
              />
            ))}
          </div>
        </div>
      </section>
      <section className="state-scene" id="overview-state">
        <div className="state-visual" aria-hidden="true">
          <div className="wave wave-a" />
          <div className="wave wave-b" />
          <div className="field-label">
            P(0) 0.50
            <br />
            P(1) 0.50
          </div>
        </div>
        <div className="state-copy">
          <p className="system-label">
            <span />
            01 / STATE SPACE
          </p>
          <h2>
            ONE QUBIT.
            <br />
            TWO <em>OUTCOMES.</em>
          </h2>
          <p>{stateExplanation}</p>
          <Link href="/learn/2" className="text-action">
            Explore superposition <b>→</b>
          </Link>
          <ListenButton
            className="mt-5"
            owner="overview-state"
            segments={[
              {
                id: "overview-state",
                title: "One qubit. Two outcomes.",
                text: stateExplanation,
                targetId: "overview-state",
              },
            ]}
          />
        </div>
      </section>
      <section className="circuit-scene" id="overview-circuit">
        <div className="circuit-copy">
          <p className="system-label">
            <span />
            02 / TRANSFORM
          </p>
          <h2>
            OPERATIONS
            <br />
            SHAPE THE <em>FIELD.</em>
          </h2>
          <p>{circuitExplanation}</p>
          <Link href="/builder" className="chrome-action">
            Build a circuit <b>↗</b>
          </Link>
          <ListenButton
            className="mt-5"
            owner="overview-circuit"
            segments={[
              {
                id: "overview-circuit",
                title: "Operations shape the field.",
                text: circuitExplanation,
                targetId: "overview-circuit",
              },
            ]}
          />
        </div>
        <div className="concept-circuit">
          <span className="circuit-name">BELL STATE / H → CNOT</span>
          <svg
            viewBox="0 0 420 210"
            role="img"
            aria-label="Bell state circuit: Hadamard on q0, then CNOT control q0 and target q1"
          >
            <g stroke="#657780" strokeWidth="1.5">
              <path d="M55 55H390M55 155H390" />
            </g>
            <g fill="#aeb7bd" fontFamily="monospace" fontSize="15">
              <text x="8" y="60">
                q0
              </text>
              <text x="8" y="160">
                q1
              </text>
            </g>
            <rect
              x="110"
              y="32"
              width="46"
              height="46"
              rx="3"
              fill="#26343c"
              stroke="#c4d4dc"
            />
            <text
              x="133"
              y="62"
              textAnchor="middle"
              fill="#f4f7f8"
              fontFamily="monospace"
              fontSize="20"
            >
              H
            </text>
            <path d="M275 55V155" stroke="#67e8ff" strokeWidth="2" />
            <circle cx="275" cy="55" r="6" fill="#67e8ff" />
            <circle
              cx="275"
              cy="155"
              r="17"
              fill="#0a0e10"
              stroke="#67e8ff"
              strokeWidth="2"
            />
            <path
              d="M263 155H287M275 143V167"
              stroke="#67e8ff"
              strokeWidth="2"
            />
          </svg>
          <span className="circuit-note">|Φ+⟩ = (|00⟩ + |11⟩) / √2</span>
        </div>
      </section>
    </div>
  );
}
