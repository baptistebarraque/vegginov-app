import { motion, useReducedMotion } from "framer-motion";
import { cn } from "../utils/cn";
import { EASE_INOUT } from "../utils/motion";

interface LogoProps {
  size?: number;
  animate?: boolean;
  className?: string;
}

// Stroke-based sprout monogram: a stem with two leaves, drawn as paths so they
// can animate on (pathLength 0 -> 1) at the admin login (docs/FRONTEND.md §6.3).
// Purely a mark — the accessible name lives on the adjacent wordmark, so the
// svg is aria-hidden.
const STEM = "M16 29 C16 23 16 19 16 14";
const LEFT_LEAF = "M16 19 C11 19 7 16 6 10 C12 9 16 12 16 19 Z";
const RIGHT_LEAF = "M16 15 C16 9 19 5 25 5 C25 11 22 15 16 15 Z";

function Logo({ size = 28, animate = false, className }: LogoProps) {
  const reduce = useReducedMotion();
  const draw = animate && !reduce;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={cn("text-pousse", className)}
    >
      {[STEM, LEFT_LEAF, RIGHT_LEAF].map((d, index) => (
        <motion.path
          key={d}
          d={d}
          initial={draw ? { pathLength: 0 } : false}
          animate={draw ? { pathLength: 1 } : undefined}
          transition={draw ? { duration: 0.6, ease: EASE_INOUT, delay: index * 0.12 } : undefined}
        />
      ))}
    </svg>
  );
}

export { Logo };
