import { Heart, ListChecks } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { getUser } from "../api/adminUsers";
import { logout } from "../api/auth";
import { AppShell } from "../components/AppShell";
import { Header } from "../components/Header";
import { Alert } from "../components/ui/Alert";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Eyebrow } from "../components/ui/Eyebrow";
import { Skeleton } from "../components/ui/Skeleton";
import { useSession } from "../hooks/useSession";
import type {
  AdminUserDetail,
  AdminUserPreferences,
  AdminUserRecipeRef,
} from "../types/adminUser";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// Read-only labels for the same vocabularies PreferenceForm offers as <select>
// options — kept here rather than shared with the form, which needs
// {value,label} pairs for editing while this view only ever renders one label.
const CALORIE_LABELS: Record<string, string> = {
  low: "Basse calorie",
  balanced: "Équilibré",
  high: "Riche (prise de masse)",
};
const DIET_LABELS: Record<string, string> = {
  omnivore: "Omnivore",
  vegetarian: "Végétarien",
  pescatarian: "Pescétarien",
  vegan: "Végane",
};
const PRICE_LABELS: Record<number, string> = {
  1: "€ — économique",
  2: "€€ — intermédiaire",
  3: "€€€ — coûteux",
};

const dateFormatter = new Intl.DateTimeFormat("fr-FR", { dateStyle: "long" });

function formatDate(isoDate: string | null): string {
  if (isoDate === null) {
    return "—";
  }
  const date = new Date(isoDate);
  return Number.isNaN(date.getTime()) ? "—" : dateFormatter.format(date);
}

function DefinitionRow({ term, value }: { term: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 border-t border-lisiere py-3 first:border-t-0 first:pt-0 sm:flex-row sm:gap-4">
      <dt className="w-56 shrink-0 text-sm text-sauge">{term}</dt>
      <dd className="text-sm text-craie">{value}</dd>
    </div>
  );
}

function PreferencesSection({ preferences }: { preferences: AdminUserPreferences | null }) {
  if (preferences === null) {
    return <p className="mt-4 text-sm text-sauge">Ce compte n’a enregistré aucune préférence.</p>;
  }

  return (
    <dl className="mt-4 max-w-[640px]">
      <DefinitionRow
        term="Orientation calorique"
        value={
          preferences.calorieOrientation === null
            ? "Non précisé"
            : (CALORIE_LABELS[preferences.calorieOrientation] ?? preferences.calorieOrientation)
        }
      />
      <DefinitionRow
        term="Régime alimentaire"
        value={
          preferences.diet === null
            ? "Non précisé"
            : (DIET_LABELS[preferences.diet] ?? preferences.diet)
        }
      />
      <DefinitionRow
        term="Allergènes à exclure"
        value={preferences.allergens.length > 0 ? preferences.allergens.join(", ") : "Aucun"}
      />
      <DefinitionRow
        term="Budget"
        value={
          preferences.priceRange === null
            ? "Non précisé"
            : (PRICE_LABELS[preferences.priceRange] ?? String(preferences.priceRange))
        }
      />
    </dl>
  );
}

function RecipeRow({ recipe, children }: { recipe: AdminUserRecipeRef; children?: ReactNode }) {
  return (
    <li className="flex items-start gap-3 border-t border-lisiere py-3 first:border-t-0 first:pt-0">
      {recipe.imageUrl && (
        <img
          src={`${API_BASE_URL}${recipe.imageUrl}`}
          alt=""
          className="size-10 shrink-0 rounded-md border border-lisiere object-cover"
        />
      )}
      <div className="flex flex-col gap-1">
        <Link
          to={`/admin/recipes/${recipe.recipeId}`}
          className="text-sm text-craie transition-colors hover:text-pousse focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
        >
          {recipe.title}
        </Link>
        {children}
      </div>
    </li>
  );
}

function AdminUserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const userId = Number(id);
  const { user: admin, isChecking: isCheckingSession } = useSession({ requireAdmin: true });
  const [account, setAccount] = useState<AdminUserDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (admin === null) {
      return;
    }
    getUser(userId)
      .then(setAccount)
      .catch(() => setLoadError("Utilisateur introuvable."));
  }, [admin, userId]);

  async function handleLogout() {
    await logout();
    navigate("/admin/login");
  }

  if (isCheckingSession || admin === null) {
    return null;
  }

  return (
    <AppShell>
      <Header
        section="Utilisateur"
        actions={
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            Se déconnecter
          </Button>
        }
      />

      <main className="pb-24">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="font-display text-3xl break-all text-craie">
            {account?.email ?? "Utilisateur"}
          </h1>
          <Link
            to="/admin/users"
            className="text-sm text-pousse transition-colors hover:text-pousse-clair focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
          >
            ← Retour à la liste
          </Link>
        </div>

        {loadError && (
          <Alert variant="error" className="mt-6 max-w-[640px]">
            {loadError}
          </Alert>
        )}

        {account === null && loadError === null && (
          <div className="mt-6 flex max-w-[640px] flex-col gap-2">
            {[0, 1, 2].map((slot) => (
              <Skeleton key={slot} className="h-14 w-full" />
            ))}
          </div>
        )}

        {account && (
          <>
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Badge variant={account.isAdmin ? "score" : "default"}>
                {account.isAdmin ? "Administrateur" : "Utilisateur"}
              </Badge>
              <span className="font-mono text-xs tracking-[0.12em] text-sauge uppercase tabular-nums">
                Inscrit le {formatDate(account.createdAt)}
              </span>
            </div>

            <section className="mt-10">
              <Eyebrow>Préférences</Eyebrow>
              <h2 className="mt-2 font-display text-2xl text-craie">Profil alimentaire</h2>
              <PreferencesSection preferences={account.preferences} />
            </section>

            <section className="mt-10">
              <Eyebrow>Ma liste</Eyebrow>
              <h2 className="mt-2 font-display text-2xl text-craie">
                Recettes gardées ({account.watchlistCount})
              </h2>
              {account.watchlist.length === 0 ? (
                <EmptyState
                  className="mt-4 max-w-[640px]"
                  icon={ListChecks}
                  title="Aucune recette gardée"
                  description="Ce compte n’a encore rien ajouté à sa liste."
                />
              ) : (
                <ul className="mt-4 max-w-[640px]">
                  {account.watchlist.map((entry) => (
                    <RecipeRow key={entry.recipeId} recipe={entry}>
                      {entry.plannedFor && (
                        <span className="font-mono text-xs text-sauge tabular-nums">
                          Prévu le {formatDate(entry.plannedFor)}
                        </span>
                      )}
                      {entry.notes && <span className="text-xs text-sauge">{entry.notes}</span>}
                    </RecipeRow>
                  ))}
                </ul>
              )}
            </section>

            <section className="mt-10">
              <Eyebrow>Coups de cœur</Eyebrow>
              <h2 className="mt-2 font-display text-2xl text-craie">
                Recettes aimées ({account.likeCount})
              </h2>
              {account.likes.length === 0 ? (
                <EmptyState
                  className="mt-4 max-w-[640px]"
                  icon={Heart}
                  title="Aucun coup de cœur"
                  description="Ce compte n’a encore aimé aucune recette."
                />
              ) : (
                <ul className="mt-4 max-w-[640px]">
                  {account.likes.map((like) => (
                    <RecipeRow key={like.recipeId} recipe={like} />
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </main>
    </AppShell>
  );
}

export default AdminUserDetailPage;
