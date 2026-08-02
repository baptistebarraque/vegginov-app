import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import {
  deleteRecipe,
  getProteinSourceOptions,
  getRecipe,
  updateRecipe,
} from "../api/adminRecipes";
import { getCurrentAdmin, logout } from "../api/auth";
import AdminRecipeForm from "../components/AdminRecipeForm";
import { AppShell } from "../components/AppShell";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { Header } from "../components/Header";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import type { AdminUser } from "../types/auth";
import type { RecipeDetail, RecipeFormValues } from "../types/recipe";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function toFormValues(recipe: RecipeDetail): RecipeFormValues {
  return {
    title: recipe.title,
    ingredients: recipe.ingredients,
    allergens: recipe.allergens,
    prepTimeMinutes: recipe.prep_time_minutes,
    servings: recipe.servings,
    proteinSource: recipe.protein_source,
    proteinGrams: recipe.protein_grams,
    caloriesPerPortion: recipe.calories_per_portion,
    priceTier: recipe.price_tier,
    instructions: recipe.instructions,
    image: null,
  };
}

function AdminRecipeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const recipeId = Number(id);
  const [admin, setAdmin] = useState<AdminUser | null>(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [recipe, setRecipe] = useState<RecipeDetail | null>(null);
  const [proteinSourceOptions, setProteinSourceOptions] = useState<string[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    getCurrentAdmin().then((current) => {
      if (current === null) {
        navigate("/admin/login");
      } else {
        setAdmin(current);
        setIsCheckingSession(false);
      }
    });
  }, [navigate]);

  useEffect(() => {
    if (admin === null) {
      return;
    }
    getRecipe(recipeId)
      .then(setRecipe)
      .catch(() => setLoadError("Recette introuvable."));
  }, [admin, recipeId]);

  useEffect(() => {
    if (admin === null) {
      return;
    }
    getProteinSourceOptions()
      .then(setProteinSourceOptions)
      .catch(() => setProteinSourceOptions([]));
  }, [admin]);

  async function handleSubmit(values: RecipeFormValues, removeExistingImage: boolean) {
    setIsSaving(true);
    setSaveError(null);
    setSaveSuccessMessage(null);
    try {
      const updated = await updateRecipe(recipeId, values, removeExistingImage);
      setRecipe(updated);
      setSaveSuccessMessage("Recette enregistrée.");
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Impossible d'enregistrer la recette.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete() {
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteRecipe(recipeId);
      navigate("/admin/recipes");
    } catch {
      setDeleteError("Impossible de supprimer la recette.");
      setIsDeleting(false);
      setIsConfirmOpen(false);
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
        section="Modifier"
        actions={
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            Se déconnecter
          </Button>
        }
      />

      <main className="pb-24">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="font-display text-3xl text-craie">Modifier la recette</h1>
          <Link
            to="/admin/recipes"
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

        {recipe && (
          <>
            <div className="mt-8">
              <AdminRecipeForm
                key={recipe.id}
                initialValues={toFormValues(recipe)}
                existingImageUrl={recipe.image_url ? `${API_BASE_URL}${recipe.image_url}` : null}
                proteinSourceOptions={proteinSourceOptions}
                onSubmit={handleSubmit}
                isLoading={isSaving}
                submitLabel="Enregistrer la recette"
                loadingLabel="Enregistrement…"
              />
            </div>

            {saveError && (
              <Alert variant="error" className="mt-4 max-w-[640px]">
                {saveError}
              </Alert>
            )}
            {saveSuccessMessage && (
              <Alert variant="success" className="mt-4 max-w-[640px]">
                {saveSuccessMessage}
              </Alert>
            )}

            <hr className="mt-12 max-w-[640px] border-lisiere" />

            <div className="mt-8 flex max-w-[640px] flex-col items-start gap-3">
              <ConfirmDialog
                open={isConfirmOpen}
                onOpenChange={setIsConfirmOpen}
                trigger={
                  <Button variant="destructive" loading={isDeleting}>
                    Supprimer la recette
                  </Button>
                }
                title="Supprimer la recette ?"
                description={`« ${recipe.title} » sera définitivement supprimée. Cette action est irréversible.`}
                confirmLabel="Supprimer"
                loading={isDeleting}
                onConfirm={handleDelete}
              />
              {deleteError && (
                <Alert variant="error" className="w-full">
                  {deleteError}
                </Alert>
              )}
            </div>
          </>
        )}
      </main>
    </AppShell>
  );
}

export default AdminRecipeDetailPage;
