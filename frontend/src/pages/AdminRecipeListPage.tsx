import { Sprout } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import { deleteRecipe, exportRecipesCsv, listRecipes } from "../api/adminRecipes";
import { logout } from "../api/auth";
import { AdminTable } from "../components/AdminTable";
import { AppShell } from "../components/AppShell";
import { Header } from "../components/Header";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Skeleton } from "../components/ui/Skeleton";
import { useSession } from "../hooks/useSession";
import type { RecipeListItem } from "../types/recipe";

function AdminRecipeListPage() {
  const { user: admin, isChecking: isCheckingSession } = useSession({ requireAdmin: true });
  const [recipes, setRecipes] = useState<RecipeListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (admin === null) {
      return;
    }
    listRecipes()
      .then(setRecipes)
      .catch(() => setError("Impossible de charger les recettes."))
      .finally(() => setIsLoading(false));
  }, [admin]);

  async function handleExport() {
    setIsExporting(true);
    setExportError(null);
    try {
      const blob = await exportRecipesCsv();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "recipes.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Recipe CSV export failed:", err);
      setExportError("Impossible de télécharger les recettes.");
    } finally {
      setIsExporting(false);
    }
  }

  async function handleDelete(id: number) {
    setDeletingId(id);
    try {
      await deleteRecipe(id);
      setRecipes((current) => current.filter((recipe) => recipe.id !== id));
    } catch {
      setError("Impossible de supprimer la recette.");
    } finally {
      setDeletingId(null);
    }
  }

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
        section="Recettes"
        actions={
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            Se déconnecter
          </Button>
        }
      />

      <main className="pb-24">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="font-display text-3xl text-craie">Recettes</h1>
          <Link
            to="/admin"
            className="text-sm text-pousse transition-colors hover:text-pousse-clair focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
          >
            ← Retour
          </Link>
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
          <Link
            to="/admin/recipes/new"
            className="inline-flex h-9 items-center rounded-md bg-pousse px-4 text-sm font-medium text-nuit transition-colors hover:bg-pousse-clair focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
          >
            Ajouter une recette
          </Link>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleExport}
            loading={isExporting}
            disabled={recipes.length === 0}
          >
            Télécharger le CSV
          </Button>
        </div>

        {exportError && (
          <Alert variant="error" className="mt-4">
            {exportError}
          </Alert>
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
          ) : recipes.length === 0 ? (
            <EmptyState
              icon={Sprout}
              title="Aucune recette pour le moment"
              description="Ajoutez votre première recette végétarienne pour la voir apparaître ici."
            />
          ) : (
            <AdminTable recipes={recipes} onDelete={handleDelete} deletingId={deletingId} />
          )}
        </div>
      </main>
    </AppShell>
  );
}

export default AdminRecipeListPage;
