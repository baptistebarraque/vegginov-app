import { type SVGProps } from "react";
import { cn } from "../../utils/cn";

// Presentational loading spinner. Loading semantics (aria-busy / aria-live)
// are owned by the caller (e.g. Button, results region), so this stays purely
// decorative and takes currentColor.
function Spinner({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg
      className={cn("animate-spin", className)}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      {...props}
    >
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
      <path
        d="M12 2a10 10 0 0 1 10 10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}

export { Spinner };
