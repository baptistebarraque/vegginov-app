import { useState, type FormEvent } from "react";

interface AdminRecipeFormProps {
  onSubmit: (
    title: string,
    ingredients: string[],
    allergens: string[],
    prepTimeMinutes: number | null,
  ) => void;
  isLoading: boolean;
}

function AdminRecipeForm({ onSubmit, isLoading }: AdminRecipeFormProps) {
  const [title, setTitle] = useState("");
  const [ingredientsText, setIngredientsText] = useState("");
  const [allergensText, setAllergensText] = useState("");
  const [prepTimeText, setPrepTimeText] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const ingredients = ingredientsText
      .split(",")
      .map((ingredient) => ingredient.trim())
      .filter(Boolean);
    const allergens = allergensText
      .split(",")
      .map((allergen) => allergen.trim())
      .filter(Boolean);
    const prepTimeMinutes = prepTimeText.trim() ? Number(prepTimeText.trim()) : null;
    onSubmit(title, ingredients, allergens, prepTimeMinutes);
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
          placeholder="Curry de lentilles corail"
          className="rounded border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-green-600 focus:outline-none dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
        />
      </label>
      <label className="flex flex-col gap-1 text-left text-sm text-neutral-700 dark:text-neutral-300">
        Ingrédients (séparés par des virgules)
        <input
          type="text"
          value={ingredientsText}
          onChange={(event) => setIngredientsText(event.target.value)}
          required
          placeholder="lentilles corail, lait de coco, curry"
          className="rounded border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-green-600 focus:outline-none dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
        />
      </label>
      <label className="flex flex-col gap-1 text-left text-sm text-neutral-700 dark:text-neutral-300">
        Allergènes (optionnel, séparés par des virgules)
        <input
          type="text"
          value={allergensText}
          onChange={(event) => setAllergensText(event.target.value)}
          placeholder="gluten, lactose"
          className="rounded border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-green-600 focus:outline-none dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
        />
      </label>
      <label className="flex flex-col gap-1 text-left text-sm text-neutral-700 dark:text-neutral-300">
        Temps de préparation en minutes (optionnel)
        <input
          type="number"
          min={0}
          value={prepTimeText}
          onChange={(event) => setPrepTimeText(event.target.value)}
          placeholder="25"
          className="rounded border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-green-600 focus:outline-none dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
        />
      </label>
      <button
        type="submit"
        disabled={isLoading}
        className="rounded bg-green-700 px-4 py-2 font-medium text-white transition hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isLoading ? "Ajout..." : "Ajouter la recette"}
      </button>
    </form>
  );
}

export default AdminRecipeForm;
