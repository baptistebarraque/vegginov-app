import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { getCurrentUser } from "../api/auth";
import type { User } from "../types/auth";

interface UseSessionOptions {
  /** Redirect non-admins away too, not just anonymous visitors. */
  requireAdmin?: boolean;
  /** Defaults to "/admin/login" when requireAdmin, else "/login". */
  redirectTo?: string;
}

// Every session-guarded page (admin panels, account/preferences/watchlist)
// repeats the same "check /auth/me on mount, redirect if it doesn't qualify"
// dance; this hook is the one place that does it.
function useSession({ requireAdmin = false, redirectTo }: UseSessionOptions = {}) {
  const [user, setUser] = useState<User | null>(null);
  const [isChecking, setIsChecking] = useState(true);
  const navigate = useNavigate();
  const target = redirectTo ?? (requireAdmin ? "/admin/login" : "/login");

  useEffect(() => {
    getCurrentUser().then((current) => {
      if (current === null || (requireAdmin && !current.isAdmin)) {
        navigate(target);
        return;
      }
      setUser(current);
      setIsChecking(false);
    });
    // Runs once on mount, same as the per-page checks it replaces — intentionally
    // not re-run if requireAdmin/redirectTo/target change on a re-render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigate]);

  return { user, isChecking };
}

export { useSession };
