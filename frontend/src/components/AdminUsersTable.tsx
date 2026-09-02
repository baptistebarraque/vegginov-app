import { Link } from "react-router";
import { cn } from "../utils/cn";
import { Badge } from "./ui/Badge";
import type { AdminUserListItem } from "../types/adminUser";

interface AdminUsersTableProps {
  users: AdminUserListItem[];
}

const dateFormatter = new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium" });

function formatSignupDate(isoDate: string): string {
  const date = new Date(isoDate);
  return Number.isNaN(date.getTime()) ? "—" : dateFormatter.format(date);
}

// Same utilitarian table as AdminTable (docs/FRONTEND.md §6.4): sticky header,
// zebra rows, a 120ms hover colour change, numerics and dates in mono. Kept a
// separate component rather than generalising AdminTable — that one owns the
// recipe delete/confirm flow, which has no counterpart here (this view is
// read-only).
function AdminUsersTable({ users }: AdminUsersTableProps) {
  return (
    <div className="w-full overflow-x-auto rounded-lg border border-lisiere">
      <table className="w-full border-collapse text-left text-sm">
        <thead>
          <tr className="sticky top-0 bg-feuille-haut">
            <th className="px-4 py-3 font-mono text-xs tracking-[0.12em] text-sauge uppercase">
              Compte
            </th>
            <th className="px-4 py-3 font-mono text-xs tracking-[0.12em] text-sauge uppercase">
              Inscription
            </th>
            <th className="px-4 py-3 text-right font-mono text-xs tracking-[0.12em] text-sauge uppercase">
              Ma liste
            </th>
            <th className="px-4 py-3 text-right font-mono text-xs tracking-[0.12em] text-sauge uppercase">
              Coups de cœur
            </th>
            <th className="px-4 py-3 font-mono text-xs tracking-[0.12em] text-sauge uppercase">
              Préférences
            </th>
            <th className="px-4 py-3 text-right font-mono text-xs tracking-[0.12em] text-sauge uppercase">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {users.map((user, index) => (
            <tr
              key={user.id}
              className={cn(
                "border-t border-lisiere transition-colors duration-[var(--dur-micro)] hover:bg-feuille-haut",
                index % 2 === 1 ? "bg-potager" : "bg-feuille",
              )}
            >
              <td className="px-4 py-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-craie">{user.email}</span>
                  {user.isAdmin && <Badge variant="score">Admin</Badge>}
                </div>
              </td>
              <td className="px-4 py-3 font-mono text-xs text-sauge tabular-nums">
                {formatSignupDate(user.createdAt)}
              </td>
              <td className="px-4 py-3 text-right font-mono text-sauge tabular-nums">
                {user.watchlistCount}
              </td>
              <td className="px-4 py-3 text-right font-mono text-sauge tabular-nums">
                {user.likeCount}
              </td>
              <td className="px-4 py-3 text-sauge">
                {user.hasPreferences ? "Renseignées" : "Aucune"}
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center justify-end">
                  <Link
                    to={`/admin/users/${user.id}`}
                    className="inline-flex h-8 items-center rounded-md px-3 text-sm text-sauge transition-colors hover:bg-feuille hover:text-craie focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
                  >
                    Voir le détail
                  </Link>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export { AdminUsersTable };
