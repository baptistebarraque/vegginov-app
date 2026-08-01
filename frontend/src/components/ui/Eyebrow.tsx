import { type HTMLAttributes } from "react";
import { cn } from "../../utils/cn";

// Mono, uppercase, wide-tracked caption in sauge (docs/FRONTEND.md §3.2).
// Shared by the hero, results header, and admin section labels.
function Eyebrow({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("font-mono text-xs tracking-[0.12em] text-sauge uppercase", className)}
      {...props}
    />
  );
}

export { Eyebrow };
