import type { Transition } from "framer-motion";

// Motion tokens (docs/FRONTEND.md §3.4). These mirror the CSS custom
// properties in index.css, expressed as the numeric seconds and cubic-bezier
// arrays framer-motion expects instead of CSS time/easing strings.
export const DURATION = {
  micro: 0.12, // hover, press, colour change
  base: 0.22, // enter/exit, route transition
  enter: 0.42, // card and section reveals
} as const;

export const EASE_OUT: [number, number, number, number] = [0.22, 1, 0.36, 1];
export const EASE_INOUT: [number, number, number, number] = [0.65, 0, 0.35, 1];

// 60ms between staggered siblings (§3.4).
export const STAGGER = 0.06;

// Card / section reveal spring shared by the results grid (§3.4).
export const CARD_SPRING: Transition = {
  type: "spring",
  stiffness: 260,
  damping: 30,
  mass: 0.8,
};
