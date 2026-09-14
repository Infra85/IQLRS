import { PageHeader, EmptyState } from "@/components/ui/page";
export default function NotFound() {
  return (
    <main className="page">
      <PageHeader
        eyebrow="404 / OUTSIDE THE LEARNING PATH"
        title="This state isn’t defined."
      />
      <EmptyState
        title="We couldn’t find that page."
        description="Return to the curriculum to choose a module, or use the navigation to open your workspace."
        href="/learn"
        action="Back to learning"
      />
    </main>
  );
}
