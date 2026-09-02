import { Users, Utensils, type LucideIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import { listRecipes } from "../api/adminRecipes";
import { listUsers } from "../api/adminUsers";
import { logout } from "../api/auth";
import { AppShell } from "../components/AppShell";
import { Header } from "../components/Header";
import { Button } from "../components/ui/Button";
import { Eyebrow } from "../components/ui/Eyebrow";
import { useSession } from "../hooks/useSession";

interface AdminSection {
  to: string;
  icon: LucideIcon;
  title: string;
  description: string;
  /** null while loading, or when the count request failed — the card still works. */
  count: number | null;
  countLabel: (count: number) => string;
}

// The admin landing screen: pick a section, nothing else. Utilitarian like the
// rest of the admin surface (docs/FRONTEND.md §6.4) — the boldness budget is
// spent on the public pages.
function AdminHomePage() {
  const { user: admin, isChecking: isCheckingSession } = useSession({ requireAdmin: true });
  const [recipeCount, setRecipeCount] = useState<number | null>(null);
  const [userCount, setUserCount] = useState<number | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (admin === null) {
      return;
    }
    // Counts are a nicety on the cards, not the point of the page: a failed
    // request just leaves them out rather than blocking navigation.
    listRecipes()
      .then((recipes) => setRecipeCount(recipes.length))
      .catch(() => setRecipeCount(null));
    listUsers()
      .then((users) => setUserCount(users.length))
      .catch(() => setUserCount(null));
  }, [admin]);

  async function handleLogout() {
    await logout();
    navigate("/admin/login");
  }

  if (isCheckingSession || admin === null) {
    return null;
  }

  const sections: AdminSection[] = [
    {
      to: "/admin/recipes",
      icon: Utensils,
      title: "Recettes",
      description: "Ajouter, modifier ou supprimer des recettes, importer et exporter un CSV.",
      count: recipeCount,
      countLabel: (count) => `${count} recette${count > 1 ? "s" : ""}`,
    },
    {
      to: "/admin/users",
      icon: Users,
      title: "Utilisateurs",
      description: "Consulter les comptes inscrits, leurs préférences et leurs recettes gardées.",
      count: userCount,
      countLabel: (count) => `${count} compte${count > 1 ? "s" : ""}`,
    },
  ];

  return (
    <AppShell>
      <Header
        section="Admin"
        actions={
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            Se déconnecter
          </Button>
        }
      />

      <main className="pb-24">
        <Eyebrow>Espace admin</Eyebrow>
        <h1 className="mt-3 font-display text-3xl text-craie">Que voulez-vous gérer ?</h1>
        <p className="mt-1 text-sm text-sauge">Connecté en tant que {admin.email}</p>

        <div className="mt-8 grid gap-4 sm:grid-cols-2">
          {sections.map(({ to, icon: Icon, title, description, count, countLabel }) => (
            <Link
              key={to}
              to={to}
              className="group flex flex-col gap-3 rounded-lg border border-lisiere bg-feuille p-6 shadow-[0_1px_2px_rgb(0_0_0/0.4)] transition-colors duration-[var(--dur-micro)] hover:border-pousse hover:bg-feuille-haut focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
            >
              <Icon
                className="size-6 text-sauge transition-colors duration-[var(--dur-micro)] group-hover:text-pousse"
                aria-hidden="true"
              />
              <h2 className="font-display text-2xl text-craie">{title}</h2>
              <p className="text-sm text-sauge">{description}</p>
              {count !== null && (
                <p className="mt-auto pt-2 font-mono text-xs tracking-[0.12em] text-sauge uppercase tabular-nums">
                  {countLabel(count)}
                </p>
              )}
            </Link>
          ))}
        </div>
      </main>
    </AppShell>
  );
}

export default AdminHomePage;
