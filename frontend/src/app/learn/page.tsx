import { ListenButton } from "@/components/narration/provider";
import { modules } from "./modules";
import ModuleItem from "./components/ModuleItem";
import { GuestPrompt } from "@/components/guest-prompt";
import { PageHeader } from "@/components/ui/page";
const introduction =
  "Start with states and measurement. Explore the algorithms. Then make the ideas operational in your own circuits.";
export default function LearnPage() {
  return (
    <main className="page">
      <GuestPrompt />
      <PageHeader
        eyebrow={`CURRICULUM / ${String(modules.length).padStart(2, "0")} MODULES`}
        title="The quantum learning path."
        description={introduction}
      />
      <div className="mb-6">
        <ListenButton
          owner="page-introduction"
          segments={[
            {
              id: "introduction",
              title: "The quantum learning path.",
              text: introduction,
            },
          ]}
          label="Listen to introduction"
        />
      </div>
      <div className="flex flex-wrap justify-between gap-3 pb-6 technical">
        <span>01—04 / Foundations</span>
        <span>05—08 / Algorithms + systems</span>
      </div>
      <section className="module-index" aria-label="Learning modules">
        {modules.map((module, index) => (
          <ModuleItem key={module.id} module={module} index={index} />
        ))}
      </section>
    </main>
  );
}
