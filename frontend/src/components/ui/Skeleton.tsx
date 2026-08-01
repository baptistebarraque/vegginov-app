import { type HTMLAttributes } from "react";
import { cn } from "../../utils/cn";

// Reserves layout space while content loads so results arrive with no CLS
// (docs/FRONTEND.md §6.2 / §9).
function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      aria-hidden="true"
      className={cn("animate-pulse rounded-md bg-feuille-haut", className)}
      {...props}
    />
  );
}

export { Skeleton };
