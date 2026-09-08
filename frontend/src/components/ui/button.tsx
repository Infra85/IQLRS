import { cva, type VariantProps } from "class-variance-authority";
import { cloneElement, isValidElement, type ButtonHTMLAttributes, type ReactElement } from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition duration-200 ease-out-expo disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]",
  {
    variants: {
      variant: {
        primary: "bg-quantum-600 text-white shadow-[0_8px_22px_rgba(76,110,245,0.28)] hover:bg-quantum-500",
        secondary: "border border-white/[0.12] bg-white/[0.06] text-slate-100 hover:border-white/[0.2] hover:bg-white/[0.1]",
        ghost: "text-slate-300 hover:bg-white/[0.07] hover:text-white",
        danger: "bg-signal-rose/15 text-rose-100 hover:bg-signal-rose/25",
      },
      size: {
        sm: "min-h-9 px-3.5 text-sm",
        md: "min-h-11 px-4 text-sm",
        lg: "min-h-12 px-5 text-base",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export function Button({ className, variant, size, asChild = false, children, ...props }: ButtonProps) {
  const classes = cn(buttonVariants({ variant, size }), className);

  if (asChild && isValidElement(children)) {
    const child = children as ReactElement<{ className?: string }>;
    return cloneElement(child, { className: cn(classes, child.props.className) });
  }

  return <button className={classes} {...props}>{children}</button>;
}
