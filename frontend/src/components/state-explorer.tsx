"use client";
import { ListenButton } from "./narration/provider";
import { useState } from "react";
import { Button } from "./ui/button";
const explanation =
  "For this real-amplitude family, |ψ⟩ = cos(θ/2)|0⟩ + sin(θ/2)|1⟩. Change θ to redistribute the measurement probabilities.";
/** A real-amplitude slice of a pure qubit state, not a full Bloch sphere. */
export function StateExplorer() {
  const [angle, setAngle] = useState(90);
  const [observed, setObserved] = useState<number | null>(null);
  const p1 = Math.sin((angle * Math.PI) / 360) ** 2;
  const feedback =
    observed === null
      ? "A measurement returns one outcome. The bars show probabilities, not two physical objects."
      : `Observed |${observed}⟩. The state is now |${observed}⟩. Prepare a new state to repeat the experiment.`;
  function update(value: number) {
    setAngle(value);
    setObserved(null);
  }
  return (
    <section
      id="state-explorer"
      className="panel overflow-hidden mb-8"
      aria-labelledby="state-explorer-title"
    >
      <div className="panel-heading">
        <h2 className="section-title" id="state-explorer-title">
          A state you can explore.
        </h2>
        <span className="technical">Interactive / 01</span>
      </div>
      <div className="state-explorer">
        <div className="state-plot">
          <svg
            viewBox="0 0 320 250"
            role="img"
            aria-label={`Probability of zero ${((1 - p1) * 100).toFixed(1)} percent; probability of one ${(p1 * 100).toFixed(1)} percent`}
          >
            <defs>
              <pattern
                id="probability-dots"
                width="6"
                height="6"
                patternUnits="userSpaceOnUse"
              >
                <circle cx="2" cy="2" r="1" fill="#9dbcc8" />
              </pattern>
            </defs>
            <path d="M35 200H285" stroke="#4b555c" />
            <rect
              x="70"
              y={200 - (1 - p1) * 155}
              width="65"
              height={(1 - p1) * 155}
              fill="url(#probability-dots)"
            />
            <rect
              x="185"
              y={200 - p1 * 155}
              width="65"
              height={p1 * 155}
              fill="url(#probability-dots)"
            />
            <g
              fill="#e9eef0"
              fontFamily="monospace"
              fontSize="14"
              textAnchor="middle"
            >
              <text x="102" y="226">
                |0⟩
              </text>
              <text x="217" y="226">
                |1⟩
              </text>
              <text x="102" y={188 - (1 - p1) * 155}>
                {((1 - p1) * 100).toFixed(1)}%
              </text>
              <text x="217" y={188 - p1 * 155}>
                {(p1 * 100).toFixed(1)}%
              </text>
            </g>
          </svg>
          <p className="technical text-center">Measurement probabilities</p>
        </div>
        <div className="p-6">
          <p className="text-sm text-slate-300 leading-7 mb-5">{explanation}</p>
          <ListenButton
            className="mb-4"
            owner="state-explorer-instructions"
            segments={[
              {
                id: "state-instructions",
                title: "Explore a quantum state",
                text: explanation,
                targetId: "state-explorer",
              },
            ]}
            label="Listen to instructions"
          />
          <label className="field" htmlFor="state-angle">
            <span className="flex justify-between">
              State angle θ <output>{angle}°</output>
            </span>
            <input
              id="state-angle"
              className="w-full accent-quantum-400 h-10"
              type="range"
              min="0"
              max="180"
              value={angle}
              onChange={(e) => update(Number(e.target.value))}
            />
          </label>
          <div className="flex gap-2 flex-wrap mt-4">
            <Button variant="secondary" size="sm" onClick={() => update(0)}>
              |0⟩
            </Button>
            <Button variant="secondary" size="sm" onClick={() => update(90)}>
              |+⟩
            </Button>
            <Button variant="secondary" size="sm" onClick={() => update(180)}>
              |1⟩
            </Button>
          </div>
          <Button
            className="mt-5"
            variant="secondary"
            onClick={() => {
              const result = Math.random() < p1 ? 1 : 0;
              setObserved(result);
              setAngle(result * 180);
            }}
          >
            Measure this state
          </Button>
          <p role="status" className="mt-4 text-sm text-slate-400 leading-6">
            {feedback}
          </p>
          <ListenButton
            className="mt-3"
            owner="state-explorer-feedback"
            segments={[
              {
                id: "state-feedback",
                title: "Measurement feedback",
                text: feedback,
                targetId: "state-explorer",
              },
            ]}
            label="Listen to feedback"
          />
        </div>
      </div>
    </section>
  );
}
