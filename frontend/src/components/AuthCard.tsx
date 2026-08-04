import { motion, useAnimationControls, useReducedMotion } from "framer-motion";
import { useEffect, type ReactNode } from "react";
import { Link } from "react-router";
import { DURATION } from "../utils/motion";
import { Logo } from "./Logo";

interface AuthCardProps {
  title: string;
  children: ReactNode;
  /** Increment to trigger a shake (e.g. on submit failure). */
  shakeTrigger?: number;
}

// Shared chrome for every auth-flow page (login, signup, admin login, password
// reset): logo, card shake-on-error, ambient glow, back-to-home link
// (docs/FRONTEND.md §6.3). One place for this instead of duplicating it per page.
function AuthCard({ title, children, shakeTrigger = 0 }: AuthCardProps) {
  const shake = useAnimationControls();
  const reduce = useReducedMotion();

  useEffect(() => {
    if (shakeTrigger > 0 && !reduce) {
      shake.start({ x: [0, -6, 6, -3, 0], transition: { duration: 0.24 } });
    }
    // Only the trigger's *change* matters, not shake/reduce identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shakeTrigger]);

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-nuit px-6">
      <Link
        to="/"
        className="absolute top-5 left-5 rounded-md px-3 py-2 text-sm text-sauge transition-colors hover:bg-feuille-haut hover:text-craie focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
      >
        Retour à l'accueil
      </Link>

      <div
        aria-hidden="true"
        className="pointer-events-none absolute top-1/2 left-1/2 h-[480px] w-[560px] max-w-full -translate-x-1/2 -translate-y-1/2"
        style={{
          background:
            "radial-gradient(circle at center, color-mix(in oklab, var(--color-pousse) 7%, transparent) 0%, transparent 68%)",
        }}
      />

      <motion.div
        initial={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.98 }}
        animate={reduce ? { opacity: 1 } : { opacity: 1, scale: 1 }}
        transition={{ duration: reduce ? 0.12 : DURATION.enter }}
        className="relative z-10 w-full max-w-[380px]"
      >
        <motion.div
          animate={shake}
          className="rounded-lg border border-lisiere bg-feuille p-8 shadow-[0_1px_2px_rgb(0_0_0/0.4)]"
        >
          <div className="flex flex-col items-center gap-3">
            <Logo size={44} animate />
            <motion.span
              initial={reduce ? { opacity: 1 } : { opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: reduce ? 0 : 0.7, duration: 0.2 }}
              className="font-display text-2xl text-craie"
            >
              Vegginov
            </motion.span>
          </div>

          <h1 className="mt-6 text-center font-display text-xl text-craie">{title}</h1>

          {children}
        </motion.div>
      </motion.div>
    </div>
  );
}

export { AuthCard };
