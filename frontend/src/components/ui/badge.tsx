import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva("inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold", {
  variants: {
    variant: {
      brand: "border-quantum-300/25 bg-quantum-500/15 text-quantum-200",
      success: "border-signal-mint/25 bg-signal-mint/10 text-emerald-200",
      warning: "border-signal-amber/25 bg-signal-amber/10 text-amber-200",
      neutral: "border-white/[0.12] bg-white/[0.06] text-slate-300",
    },
  },
  defaultVariants: { variant: "neutral" },
});

export function Badge({ className, variant, ...props }: React.HTMLAttributes<HTMLSpanElement> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
