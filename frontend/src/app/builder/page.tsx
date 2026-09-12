import { ListenButton } from "@/components/narration/provider";
import { Suspense } from "react";
import CircuitBuilder from "@/components/circuit-builder/CircuitBuilder";
import { GuestPrompt } from "@/components/guest-prompt";
import { PageHeader, LoadingState } from "@/components/ui/page";
import { Badge } from "@/components/ui/badge";
const introduction =
  "Choose a gate, place it on a qubit wire, and observe how your circuit changes the state. Every experiment starts with |0⟩.";
export default function BuilderPage() {
  return (
    <main className="page">
      <GuestPrompt />
      <PageHeader
        eyebrow="LAB / 01 — CIRCUIT INSTRUMENT"
        title="Build a quantum circuit."
        description={introduction}
        action={<Badge>QISKIT / SIMULATOR</Badge>}
      />
      <div className="mb-6">
        <ListenButton
          owner="page-introduction"
          segments={[
            {
              id: "introduction",
              title: "Build a quantum circuit.",
              text: introduction,
            },
          ]}
          label="Listen to introduction"
        />
      </div>
      <Suspense
        fallback={<LoadingState label="Preparing circuit instrument…" />}
      >
        <CircuitBuilder />
      </Suspense>
    </main>
  );
}
