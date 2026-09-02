import { Users } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import { listUsers } from "../api/adminUsers";
import { logout } from "../api/auth";
import { AdminUsersTable } from "../components/AdminUsersTable";
import { AppShell } from "../components/AppShell";
import { Header } from "../components/Header";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Skeleton } from "../components/ui/Skeleton";
import { useSession } from "../hooks/useSession";
import type { AdminUserListItem } from "../types/adminUser";

function AdminUsersPage() {
  const { user: admin, isChecking: isCheckingSession } = useSession({ requireAdmin: true });
  const [users, setUsers] = useState<AdminUserListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (admin === null) {
      return;
    }
    listUsers()
      .then(setUsers)
      .catch(() => setError("Impossible de charger les utilisateurs."))
      .finally(() => setIsLoading(false));
  }, [admin]);

  async function handleLogout() {
    await logout();
    navigate("/admin/login");
  }

  if (isCheckingSession || admin === null) {
    return null;
  }

  const adminCount = users.filter((user) => user.isAdmin).length;

  return (
    <AppShell>
      <Header
        section="Utilisateurs"
        actions={
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            Se déconnecter
          </Button>
        }
      />

      <main className="pb-24">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="font-display text-3xl text-craie">Utilisateurs</h1>
          <Link
            to="/admin"
            className="text-sm text-pousse transition-colors hover:text-pousse-clair focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
          >
            ← Retour
          </Link>
        </div>

        {!isLoading && error === null && users.length > 0 && (
          <p className="mt-2 text-sm text-sauge">
            {users.length} compte{users.length > 1 ? "s" : ""}, dont {adminCount} administrateur
            {adminCount > 1 ? "s" : ""}.
          </p>
        )}

        <div className="mt-6">
          {isLoading ? (
            <div className="flex flex-col gap-2">
              {[0, 1, 2, 3].map((slot) => (
                <Skeleton key={slot} className="h-14 w-full" />
              ))}
            </div>
          ) : error ? (
            <Alert variant="error">{error}</Alert>
          ) : users.length === 0 ? (
            <EmptyState
              icon={Users}
              title="Aucun compte pour le moment"
              description="Les comptes créés depuis la page d'inscription apparaîtront ici."
            />
          ) : (
            <AdminUsersTable users={users} />
          )}
        </div>
      </main>
    </AppShell>
  );
}

export default AdminUsersPage;
