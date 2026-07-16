import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { createRecipe } from "../api/adminRecipes";
import { getCurrentAdmin, logout } from "../api/auth";
import AdminRecipeForm from "../components/AdminRecipeForm";
import type { AdminUser } from "../types/auth";

function AdminUploadPage() {
  const [admin, setAdmin] = useState<AdminUser | null>(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
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

  async function handleSubmit(
    title: string,
    ingredients: string[],
    allergens: string[],
    prepTimeMinutes: number | null,
  ) {
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const recipe = await createRecipe(title, ingredients, allergens, prepTimeMinutes);
      setSuccessMessage(`Recette ajoutée : ${recipe.title}`);
    } catch {
      setError("Impossible d'ajouter la recette.");
    } finally {
      setIsSubmitting(false);
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
          Ajouter une recette
        </h1>
        <button
          type="button"
          onClick={handleLogout}
          className="text-sm text-neutral-500 underline hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200"
        >
          Déconnexion
        </button>
      </div>
      <p className="text-neutral-600 dark:text-neutral-300">Connecté en tant que {admin.email}</p>

      <AdminRecipeForm onSubmit={handleSubmit} isLoading={isSubmitting} />

      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      {successMessage && (
        <p className="text-sm text-green-700 dark:text-green-400">{successMessage}</p>
      )}
    </main>
  );
}

export default AdminUploadPage;
