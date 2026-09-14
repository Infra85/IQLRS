import { cva, type VariantProps } from "class-variance-authority";
import {
  cloneElement,
  isValidElement,
  type ButtonHTMLAttributes,
  type ReactElement,
} from "react";
import { cn } from "@/lib/utils";
const buttonVariants = cva("ui-button", {
  variants: {
    variant: {
      primary: "button-primary",
      secondary: "button-secondary",
      ghost: "button-ghost",
      danger: "button-danger",
    },
    size: { sm: "px-3 text-xs", md: "", lg: "min-h-12 px-5" },
  },
  defaultVariants: { variant: "primary", size: "md" },
});
export interface ButtonProps
  extends
    ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}
export function Button({
  className,
  variant,
  size,
  asChild = false,
  children,
  ...props
}: ButtonProps) {
  const classes = cn(buttonVariants({ variant, size }), className);
  if (asChild && isValidElement(children)) {
    const child = children as ReactElement<{ className?: string }>;
    return cloneElement(child, {
      ...props,
      className: cn(classes, child.props.className),
    });
  }
  return (
    <button type="button" className={classes} {...props}>
      {children}
    </button>
  );
}
