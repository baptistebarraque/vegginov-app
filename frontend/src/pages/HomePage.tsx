import { useState } from "react";
import { fetchSuggestions } from "../api/suggestions";
import RecipeForm from "../components/RecipeForm";
import SuggestionList from "../components/SuggestionList";
import type { RecipeSuggestion } from "../types/recipe";

function HomePage() {
  const [suggestions, setSuggestions] = useState<RecipeSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  async function handleSubmit(title: string, ingredients: string[]) {
    setIsLoading(true);
    setError(null);
    setHasSearched(true);
    try {
      const response = await fetchSuggestions(title, ingredients);
      setSuggestions(response.suggestions);
    } catch {
      setError("Impossible de récupérer des suggestions pour le moment.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center gap-6 bg-white px-4 py-12 dark:bg-neutral-900">
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-3xl font-semibold text-green-800 dark:text-green-400">Veggie App</h1>
        <p className="text-neutral-600 dark:text-neutral-300">
          Trouvez des recettes végétariennes qui ressemblent à vos plats préférés.
        </p>
      </div>

      <RecipeForm onSubmit={handleSubmit} isLoading={isLoading} />

      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

      {!isLoading && hasSearched && !error && suggestions.length === 0 && (
        <p className="text-sm text-neutral-500 dark:text-neutral-400">Aucune suggestion trouvée.</p>
      )}

      <SuggestionList suggestions={suggestions} />
    </main>
  );
}

export default HomePage;
