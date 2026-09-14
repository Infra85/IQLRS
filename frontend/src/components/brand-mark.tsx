import { cn } from "@/lib/utils";
export function BrandMark({
  className,
  compact = false,
}: {
  className?: string;
  compact?: boolean;
}) {
  return (
    <span className={cn("inline-flex items-center gap-3", className)}>
      <span className="brand-symbol" aria-hidden="true">
        |ψ⟩
      </span>
      {!compact && (
        <span className="text-sm font-semibold tracking-[.12em] text-white">
          IQLRS
          <span className="hidden lg:block text-[9px] font-normal tracking-[.18em] text-slate-400">
            QUANTUM LEARNING
          </span>
        </span>
      )}
    </span>
  );
}
