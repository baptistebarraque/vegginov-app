import { type ReactNode } from "react";
import { cn } from "../utils/cn";

interface AppShellProps {
  children: ReactNode;
  className?: string;
}

// Page background (deepest nuit layer) + the 1100px content column with the
// standard gutters: 24px on mobile, 48px on desktop (docs/FRONTEND.md §3.3).
function AppShell({ children, className }: AppShellProps) {
  return (
    <div className={cn("min-h-screen bg-nuit text-craie", className)}>
      <div className="mx-auto w-full max-w-[1100px] px-6 md:px-12">{children}</div>
    </div>
  );
}

export { AppShell };
