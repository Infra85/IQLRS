import { ListenButton, NarratorOnly } from "@/components/narration/provider";
import { Suspense } from "react";
import CircuitBuilder from "@/components/circuit-builder/CircuitBuilder";
import { GuestPrompt } from "@/components/guest-prompt";
import { PageHeader, LoadingState } from "@/components/ui/page";
import { Badge } from "@/components/ui/badge";
const introduction =
  "Choose a gate, place it on a qubit wire, and observe how your circuit changes the state. All qubits start in |0⟩.";
export default async function BuilderPage({ searchParams }: { searchParams: Promise<{ module?: string; challenge?: string }> }) {
  const context = await searchParams;
  const activity = Boolean(context.module || context.challenge);
  const title = activity ? "Learn through experimentation." : "Quantum Circuit Builder";
  const description = activity ? "Commit a prediction, explore your idea, and use feedback to refine your understanding." : introduction;
  return (
    <main className="page">
      <GuestPrompt />
      <PageHeader
        eyebrow={activity ? "LAB / LEARNING ACTIVITIES" : "LAB / 01 — CIRCUIT INSTRUMENT"}
        title={title}
        description={description}
        action={<Badge>{activity ? "GUIDED LEARNING" : "QISKIT / SIMULATOR"}</Badge>}
      />
      <NarratorOnly>
        <div className="mb-6">
          <ListenButton
            owner="page-introduction"
            segments={[
              {
                id: "introduction",
                title,
                text: description,
              },
            ]}
            label="Listen to introduction"
          />
        </div>
      </NarratorOnly>
      <Suspense
        fallback={<LoadingState label="Preparing circuit instrument…" />}
      >
        <CircuitBuilder key={JSON.stringify([context.module ?? null, context.challenge ?? null])} />
      </Suspense>
    </main>
  );
}
