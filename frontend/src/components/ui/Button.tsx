import { cva, type VariantProps } from "class-variance-authority";
import { forwardRef, type ButtonHTMLAttributes } from "react";
import { cn } from "../../utils/cn";
import { Spinner } from "./Spinner";

// Elevation is surface + border, not heavy shadow (docs/FRONTEND.md §3.1); the
// single soft glow allowed in this pass is the primary button's focus ring.
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors duration-[var(--dur-micro)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse disabled:cursor-not-allowed",
  {
    variants: {
      variant: {
        primary:
          "bg-pousse text-nuit hover:bg-pousse-clair focus-visible:ring-4 focus-visible:ring-pousse/25 disabled:bg-pousse-sourd",
        secondary:
          "border border-lisiere bg-feuille-haut text-craie hover:border-pousse/50 disabled:opacity-60",
        ghost: "text-sauge hover:bg-feuille-haut hover:text-craie disabled:opacity-60",
        destructive: "bg-brique text-craie hover:brightness-110 disabled:opacity-60",
      },
      size: {
        sm: "h-8 px-3 text-sm",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-6 text-base",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading = false, disabled, children, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size }), className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && <Spinner className="size-4" />}
      {children}
    </button>
  ),
);
Button.displayName = "Button";

export { Button };
