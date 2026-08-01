import { cva, type VariantProps } from "class-variance-authority";
import { type HTMLAttributes } from "react";
import { cn } from "../../utils/cn";

// Minimal inline alert — the toast substitute for this pass (docs/FRONTEND.md
// §5). Announced politely; error copy says what happened, never a bare apology.
const alertVariants = cva("rounded-md border px-4 py-3 text-sm", {
  variants: {
    variant: {
      error: "border-brique/40 bg-brique/10 text-craie",
      info: "border-lisiere bg-feuille-haut text-sauge",
      success: "border-pousse/40 bg-pousse/10 text-craie",
    },
  },
  defaultVariants: { variant: "info" },
});

interface AlertProps extends HTMLAttributes<HTMLDivElement>, VariantProps<typeof alertVariants> {}

function Alert({ className, variant, ...props }: AlertProps) {
  return (
    <div
      role="alert"
      aria-live="polite"
      className={cn(alertVariants({ variant }), className)}
      {...props}
    />
  );
}

export { Alert };
