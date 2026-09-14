"use client";
import { PageHeader, Status } from "@/components/ui/page";
import { Button } from "@/components/ui/button";
export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="page">
      <PageHeader
        eyebrow="SYSTEM / INTERRUPTED"
        title="Let’s try that again."
      />
      <Status kind="error">
        This page couldn’t be loaded. Try again to restore your workspace.
      </Status>
      <Button className="mt-5" onClick={reset}>
        Try again
      </Button>
    </main>
  );
}
