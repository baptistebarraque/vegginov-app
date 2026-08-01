import { motion, useReducedMotion } from "framer-motion";
import { type ReactNode } from "react";
import { DURATION, EASE_OUT } from "../utils/motion";

interface RevealProps {
  children: ReactNode;
  delay?: number;
  className?: string;
}

// Section reveal: y + blur fade-up on mount, opacity-only and capped at 120ms
// under reduced motion (docs/FRONTEND.md §7). Shared by the hero sequence and
// the results section so the reduced-motion rule lives in one place.
function Reveal({ children, delay = 0, className }: RevealProps) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduce ? { opacity: 0 } : { opacity: 0, y: 12, filter: "blur(6px)" }}
      animate={reduce ? { opacity: 1 } : { opacity: 1, y: 0, filter: "blur(0px)" }}
      transition={{
        duration: reduce ? 0.12 : DURATION.enter,
        ease: EASE_OUT,
        delay: reduce ? 0 : delay,
      }}
    >
      {children}
    </motion.div>
  );
}

export { Reveal };
