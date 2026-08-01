import { forwardRef, type HTMLAttributes } from "react";
import { cn } from "../../utils/cn";

// Elevation = feuille surface + 1px lisiere border + the single allowed max
// shadow (docs/FRONTEND.md §3.1), never a heavy glow.
const Card = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "rounded-lg border border-lisiere bg-feuille shadow-[0_1px_2px_rgb(0_0_0/0.4)]",
        className,
      )}
      {...props}
    />
  ),
);
Card.displayName = "Card";

export { Card };
