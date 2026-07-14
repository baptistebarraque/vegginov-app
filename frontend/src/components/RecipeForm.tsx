import { useState, type FormEvent } from "react";

interface RecipeFormProps {
  onSubmit: (title: string, ingredients: string[]) => void;
  isLoading: boolean;
}

function RecipeForm({ onSubmit, isLoading }: RecipeFormProps) {
  const [title, setTitle] = useState("");
  const [ingredientsText, setIngredientsText] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const ingredients = ingredientsText
      .split(",")
      .map((ingredient) => ingredient.trim())
      .filter(Boolean);
    onSubmit(title, ingredients);
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-md flex-col gap-3">
      <label className="flex flex-col gap-1 text-left text-sm text-neutral-700 dark:text-neutral-300">
        Nom de la recette
        <input
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          required
          placeholder="Poulet au curry"
          className="rounded border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-green-600 focus:outline-none dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
        />
      </label>
      <label className="flex flex-col gap-1 text-left text-sm text-neutral-700 dark:text-neutral-300">
        Ingrédients (séparés par des virgules)
        <input
          type="text"
          value={ingredientsText}
          onChange={(event) => setIngredientsText(event.target.value)}
          placeholder="poulet, curry, lait de coco"
          className="rounded border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-green-600 focus:outline-none dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
        />
      </label>
      <button
        type="submit"
        disabled={isLoading}
        className="rounded bg-green-700 px-4 py-2 font-medium text-white transition hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isLoading ? "Recherche..." : "Trouver des recettes"}
      </button>
    </form>
  );
}

export default RecipeForm;
