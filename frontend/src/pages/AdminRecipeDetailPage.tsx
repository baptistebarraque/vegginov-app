import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { deleteRecipe, getRecipe, updateRecipe } from "../api/adminRecipes";
import { getCurrentAdmin, logout } from "../api/auth";
import AdminRecipeForm from "../components/AdminRecipeForm";
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
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
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
    if (!window.confirm(`Supprimer la recette "${recipe?.title}" ? Cette action est définitive.`)) {
      return;
    }
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteRecipe(recipeId);
      navigate("/admin/recipes");
    } catch {
      setDeleteError("Impossible de supprimer la recette.");
      setIsDeleting(false);
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
    <main className="flex min-h-screen flex-col items-center gap-6 bg-white px-4 py-12 dark:bg-neutral-900">
      <div className="flex w-full max-w-md items-center justify-between">
        <h1 className="text-3xl font-semibold text-green-800 dark:text-green-400">
          Modifier la recette
        </h1>
        <button
          type="button"
          onClick={handleLogout}
          className="text-sm text-neutral-500 underline hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200"
        >
          Déconnexion
        </button>
      </div>
      <Link
        to="/admin/recipes"
        className="self-start text-sm text-green-700 underline hover:text-green-800 dark:text-green-400 dark:hover:text-green-300"
      >
        ← Retour à la liste
      </Link>

      {loadError && <p className="text-sm text-red-600 dark:text-red-400">{loadError}</p>}

      {recipe && (
        <>
          <AdminRecipeForm
            key={recipe.id}
            initialValues={toFormValues(recipe)}
            existingImageUrl={recipe.image_url ? `${API_BASE_URL}${recipe.image_url}` : null}
            onSubmit={handleSubmit}
            isLoading={isSaving}
            submitLabel="Enregistrer"
            loadingLabel="Enregistrement..."
          />

          {saveError && <p className="text-sm text-red-600 dark:text-red-400">{saveError}</p>}
          {saveSuccessMessage && (
            <p className="text-sm text-green-700 dark:text-green-400">{saveSuccessMessage}</p>
          )}

          <hr className="w-full max-w-md border-neutral-300 dark:border-neutral-700" />

          <button
            type="button"
            onClick={handleDelete}
            disabled={isDeleting}
            className="rounded bg-red-700 px-4 py-2 font-medium text-white transition hover:bg-red-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isDeleting ? "Suppression..." : "Supprimer la recette"}
          </button>
          {deleteError && <p className="text-sm text-red-600 dark:text-red-400">{deleteError}</p>}
        </>
      )}
    </main>
  );
}

export default AdminRecipeDetailPage;
