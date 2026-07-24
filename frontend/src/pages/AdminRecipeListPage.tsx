import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import { listRecipes } from "../api/adminRecipes";
import { getCurrentAdmin, logout } from "../api/auth";
import type { AdminUser } from "../types/auth";
import type { RecipeListItem } from "../types/recipe";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function AdminRecipeListPage() {
  const [admin, setAdmin] = useState<AdminUser | null>(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);
  const [recipes, setRecipes] = useState<RecipeListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
    listRecipes()
      .then(setRecipes)
      .catch(() => setError("Impossible de charger les recettes."))
      .finally(() => setIsLoading(false));
  }, [admin]);

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
        <h1 className="text-3xl font-semibold text-green-800 dark:text-green-400">Recettes</h1>
        <button
          type="button"
          onClick={handleLogout}
          className="text-sm text-neutral-500 underline hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200"
        >
          Déconnexion
        </button>
      </div>
      <Link
        to="/admin"
        className="self-start text-sm text-green-700 underline hover:text-green-800 dark:text-green-400 dark:hover:text-green-300"
      >
        Ajouter une recette
      </Link>

      {isLoading && <p className="text-sm text-neutral-500 dark:text-neutral-400">Chargement...</p>}
      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      {!isLoading && !error && recipes.length === 0 && (
        <p className="text-sm text-neutral-500 dark:text-neutral-400">Aucune recette pour le moment.</p>
      )}

      <ul className="flex w-full max-w-md flex-col gap-2">
        {recipes.map((recipe) => (
          <li key={recipe.id}>
            <Link
              to={`/admin/recipes/${recipe.id}`}
              className="flex items-center gap-3 rounded border border-neutral-200 px-3 py-2 hover:border-green-600 dark:border-neutral-700 dark:hover:border-green-500"
            >
              {recipe.image_url && (
                <img
                  src={`${API_BASE_URL}${recipe.image_url}`}
                  alt=""
                  className="h-12 w-12 rounded object-cover"
                />
              )}
              <span className="text-neutral-900 dark:text-white">{recipe.title}</span>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}

export default AdminRecipeListPage;
