import { cva, type VariantProps } from "class-variance-authority";
import { type HTMLAttributes } from "react";
import { cn } from "../../utils/cn";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-pill px-2.5 py-0.5 text-xs font-medium",
  {
    variants: {
      variant: {
        default: "bg-feuille-haut text-sauge",
        // Marks the source (non-veg) recipe; semantic, at most twice per screen.
        accent: "bg-betterave/15 text-betterave",
        // Numeric data (e.g. similarity score) reads in mono (docs/FRONTEND.md §3.2).
        score: "bg-pousse/15 font-mono text-pousse tabular-nums",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge };
