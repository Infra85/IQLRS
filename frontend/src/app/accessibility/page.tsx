import { NarratorSetting } from "@/components/narration/provider";
import { PageHeader } from "@/components/ui/page";

export default function AccessibilityPage() {
  return (
    <main className="page">
      <PageHeader
        eyebrow="PREFERENCES"
        title="Accessibility"
        description="Choose how you experience the learning platform."
      />
      <NarratorSetting />
    </main>
  );
}
