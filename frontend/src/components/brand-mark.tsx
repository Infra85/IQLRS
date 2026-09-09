import { cn } from "@/lib/utils";

type BrandMarkProps = {
  className?: string;
  compact?: boolean;
};

export function BrandMark({ className, compact = false }: BrandMarkProps) {
  return (
    <div className={cn("inline-flex items-center gap-2.5", className)}>
      <span
        aria-hidden="true"
        className="relative grid h-9 w-9 place-items-center overflow-hidden rounded-xl border border-quantum-300/35 bg-gradient-to-br from-quantum-500 to-quantum-800 shadow-glow"
      >
        <span className="absolute h-5 w-5 rounded-full border border-white/70" />
        <span className="absolute h-1.5 w-1.5 rounded-full bg-signal-cyan shadow-[0_0_12px_2px_rgba(48,201,215,0.9)]" />
        <span className="absolute h-9 w-4 rotate-45 rounded-full border-x border-white/35" />
      </span>
      {!compact && (
        <span className="text-base font-semibold tracking-[-0.025em] text-white">
          IQ<span className="text-quantum-500">LRS</span>
        </span>
      )}
    </div>
  );
}
