import { type ReactNode } from "react";
import { Link } from "react-router";
import { cn } from "../utils/cn";
import { Logo } from "./Logo";

interface HeaderProps {
  section?: string;
  actions?: ReactNode;
  className?: string;
}

// Wordmark left, an optional current-section label, and right-side actions
// (docs/FRONTEND.md §6.4). Kept quiet on every screen — the boldness budget is
// spent on the public hero.
function Header({ section, actions, className }: HeaderProps) {
  return (
    <header className={cn("flex items-center justify-between gap-4 py-5", className)}>
      <div className="flex items-center gap-3">
        <Link
          to="/"
          className="flex items-center gap-2 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
        >
          <Logo size={26} />
          <span className="font-display text-lg text-craie">Vegginov</span>
        </Link>
        {section && (
          <>
            <span className="text-lisiere" aria-hidden="true">
              /
            </span>
            <span className="font-mono text-xs tracking-[0.12em] text-sauge uppercase">
              {section}
            </span>
          </>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  );
}

export { Header };
