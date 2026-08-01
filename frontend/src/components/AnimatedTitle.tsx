import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useEffect, useState } from "react";
import { cn } from "../utils/cn";
import { DURATION, EASE_OUT } from "../utils/motion";

interface AnimatedTitleProps {
  prefix: string;
  words: string[];
  suffix: string;
  intervalMs?: number;
  className?: string;
}

// The one signature effect (docs/FRONTEND.md §6.1): the highlighted noun cycles
// through a French list; the width animates via layout so the line never jumps.
// Accessibility: a visually-hidden span carries the full sentence as one clean
// string for screen readers, and the animated per-word visual layer is
// aria-hidden so the word-swap never fragments reading order. Under reduced
// motion the first word is shown statically with no loop.
function AnimatedTitle({ prefix, words, suffix, intervalMs = 3200, className }: AnimatedTitleProps) {
  const reduce = useReducedMotion();
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (reduce || words.length <= 1) {
      return;
    }
    const id = window.setInterval(
      () => setIndex((current) => (current + 1) % words.length),
      intervalMs,
    );
    return () => window.clearInterval(id);
  }, [reduce, words.length, intervalMs]);

  const current = words[index] ?? "";

  return (
    <h1
      className={cn(
        "text-[clamp(2.25rem,6vw,4rem)] font-display text-craie",
        className,
      )}
    >
      <span className="sr-only">{`${prefix} ${current}${suffix}`}</span>
      <span aria-hidden="true">
        {prefix}{" "}
        <span className="relative inline-flex text-betterave">
          <AnimatePresence mode="popLayout" initial={false}>
            <motion.span
              key={current}
              className="inline-block whitespace-nowrap"
              initial={reduce ? false : { y: 14, opacity: 0, filter: "blur(4px)" }}
              animate={reduce ? { opacity: 1 } : { y: 0, opacity: 1, filter: "blur(0px)" }}
              exit={reduce ? { opacity: 0 } : { y: -14, opacity: 0, filter: "blur(4px)" }}
              transition={{ duration: DURATION.base, ease: EASE_OUT }}
            >
              {current}
            </motion.span>
          </AnimatePresence>
        </span>
        {suffix}
      </span>
    </h1>
  );
}

export { AnimatedTitle };
