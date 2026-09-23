import { Activity, ArrowRight } from "lucide-react";
import Link from "next/link";
import { Button } from "./button";
import { cn } from "@/lib/utils";
export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        <p className="system-label">
          <span />
          {eyebrow}
        </p>
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </header>
  );
}
export function Status({
  children,
  kind = "info",
}: {
  children: React.ReactNode;
  kind?: "info" | "error" | "success";
}) {
  return (
    <div
      role={kind === "error" ? "alert" : "status"}
      className={cn(
        "status",
        kind === "error" && "status-error",
        kind === "success" && "status-success",
      )}
    >
      {children}
    </div>
  );
}
export function LoadingState({
  label = "Loading workspace…",
}: {
  label?: string;
}) {
  return (
    <div role="status" aria-label={label} className="space-y-5 py-8">
      <p className="technical">{label}</p>
      <div className="skeleton h-10 w-2/3" />
      <div className="grid grid-cols-2 gap-4">
        <div className="skeleton h-32" />
        <div className="skeleton h-32" />
      </div>
      <span className="sr-only">Please wait.</span>
    </div>
  );
}
export function EmptyState({
  title,
  description,
  href,
  action,
}: {
  title: string;
  description: string;
  href?: string;
  action?: string;
}) {
  return (
    <div className="empty-state">
      <Activity size={28} aria-hidden="true" />
      <h2>{title}</h2>
      <p>{description}</p>
      {href && (
        <Button asChild variant="secondary">
          <Link href={href}>
            {action || "Explore modules"}
            <ArrowRight size={16} />
          </Link>
        </Button>
      )}
    </div>
  );
}
