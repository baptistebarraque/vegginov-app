import { motion } from "framer-motion";
import { useEffect, useRef } from "react";
import IngredientBurst from "./IngredientBurst";
import type { RecipeSuggestion } from "../types/recipe";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface RecipeDetailPanelProps {
  suggestion: RecipeSuggestion;
  onClose: () => void;
}

function RecipeDetailPanel({ suggestion, onClose }: RecipeDetailPanelProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeButtonRef.current?.focus();
  }, []);

  return (
    <motion.div
      className="fixed inset-0 z-30 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
    >
      <div className="w-full max-w-lg" onClick={(event) => event.stopPropagation()}>
        <motion.div
          role="dialog"
          aria-modal="true"
          aria-labelledby="recipe-detail-title"
          className="max-h-full w-full overflow-y-auto rounded-lg bg-white p-6 dark:bg-neutral-900"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.2 }}
        >
          <div className="flex items-start justify-between gap-4">
            <h2
              id="recipe-detail-title"
              className="text-xl font-semibold text-green-800 dark:text-green-400"
            >
              {suggestion.title}
            </h2>
            <button
              ref={closeButtonRef}
              type="button"
              onClick={onClose}
              aria-label="Fermer"
              className="text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200"
            >
              ✕
            </button>
          </div>

          {suggestion.image_url && (
            <img
              src={`${API_BASE_URL}${suggestion.image_url}`}
              alt={suggestion.title}
              className="mx-auto mt-4 max-h-56 w-auto object-contain"
            />
          )}

          <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-neutral-600 dark:text-neutral-400">
            {suggestion.prep_time_minutes !== null && (
              <>
                <dt className="font-medium">Préparation</dt>
                <dd>{suggestion.prep_time_minutes} min</dd>
              </>
            )}
            {suggestion.servings !== null && (
              <>
                <dt className="font-medium">Portions</dt>
                <dd>{suggestion.servings}</dd>
              </>
            )}
            {suggestion.protein_source !== null && (
              <>
                <dt className="font-medium">Source de protéines</dt>
                <dd>{suggestion.protein_source}</dd>
              </>
            )}
          </dl>

          {(suggestion.allergens ?? []).length > 0 && (
            <p className="mt-4 text-sm text-red-700 dark:text-red-400">
              Allergènes : {suggestion.allergens.join(", ")}
            </p>
          )}

          <h3 className="mt-4 font-medium text-neutral-900 dark:text-white">Ingrédients</h3>
          <ul className="mt-1 list-disc pl-5 text-sm text-neutral-700 dark:text-neutral-300">
            {(suggestion.ingredients ?? []).map((ingredient, index) => (
              <li key={`${ingredient.name}-${index}`}>
                {ingredient.name}
                {ingredient.quantity ? ` — ${ingredient.quantity}` : ""}
              </li>
            ))}
          </ul>

          {(suggestion.instructions ?? []).length > 0 && (
            <>
              <h3 className="mt-4 font-medium text-neutral-900 dark:text-white">Préparation</h3>
              <ol className="mt-1 list-decimal pl-5 text-sm text-neutral-700 dark:text-neutral-300">
                {suggestion.instructions.map((step, index) => (
                  <li key={index}>{step}</li>
                ))}
              </ol>
            </>
          )}
        </motion.div>
      </div>

      <IngredientBurst ingredients={suggestion.ingredients ?? []} />
    </motion.div>
  );
}

export default RecipeDetailPanel;
