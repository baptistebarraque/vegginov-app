import { motion } from "framer-motion";
import { X } from "lucide-react";
import { useEffect, useRef } from "react";
import IngredientBurst from "./IngredientBurst";
import { Badge } from "./ui/Badge";
import { WatchlistButton } from "./WatchlistButton";
import type { RecipeSuggestion } from "../types/recipe";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

/** Cost tier (1..3) rendered as €/€€/€€€ — see price_tier on the backend. */
function priceTierLabel(tier: number): string {
  return "€".repeat(tier);
}

interface RecipeDetailPanelProps {
  suggestion: RecipeSuggestion;
  onClose: () => void;
  /** Omitted entirely (no button rendered) when the user is anonymous. */
  onToggleWatchlist?: () => void;
}

function RecipeDetailPanel({ suggestion, onClose, onToggleWatchlist }: RecipeDetailPanelProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeButtonRef.current?.focus();
  }, []);

  return (
    <motion.div
      className="fixed inset-0 z-30 flex items-center justify-center bg-nuit/80 p-4"
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
          className="max-h-[85vh] w-full overflow-y-auto overscroll-contain rounded-lg border border-lisiere bg-feuille p-6 shadow-[0_1px_2px_rgb(0_0_0/0.4)]"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.2 }}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex flex-col items-start gap-2">
              <h2 id="recipe-detail-title" className="font-display text-2xl text-craie">
                {suggestion.title}
              </h2>
              <Badge variant="score">{Math.round(suggestion.score * 100)} % de proximité</Badge>
            </div>
            <div className="flex items-center gap-1">
              {onToggleWatchlist && (
                <WatchlistButton
                  isWatchlisted={suggestion.is_watchlisted}
                  onToggle={onToggleWatchlist}
                />
              )}
              <button
                ref={closeButtonRef}
                type="button"
                onClick={onClose}
                aria-label="Fermer"
                className="rounded-sm text-sauge transition-colors hover:text-craie focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
              >
                <X className="size-5" aria-hidden="true" />
              </button>
            </div>
          </div>

          {suggestion.image_url && (
            <img
              src={`${API_BASE_URL}${suggestion.image_url}`}
              alt={suggestion.title}
              className="mx-auto mt-4 max-h-56 w-auto object-contain"
            />
          )}

          <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-sauge">
            {suggestion.prep_time_minutes !== null && (
              <>
                <dt className="font-medium text-sauge">Préparation</dt>
                <dd className="font-mono text-craie">{suggestion.prep_time_minutes} min</dd>
              </>
            )}
            {suggestion.servings !== null && (
              <>
                <dt className="font-medium text-sauge">Portions</dt>
                <dd className="font-mono text-craie">{suggestion.servings}</dd>
              </>
            )}
            {suggestion.protein_source !== null && (
              <>
                <dt className="font-medium text-sauge">Source de protéines</dt>
                <dd className="text-craie">{suggestion.protein_source}</dd>
              </>
            )}
            {suggestion.protein_grams !== null && (
              <>
                <dt className="font-medium text-sauge">Protéines (par portion)</dt>
                <dd className="font-mono text-craie">{suggestion.protein_grams} g</dd>
              </>
            )}
            {suggestion.calories_per_portion !== null && (
              <>
                <dt className="font-medium text-sauge">Calories (par portion)</dt>
                <dd className="font-mono text-craie">{suggestion.calories_per_portion} kcal</dd>
              </>
            )}
            {suggestion.protein_density !== null && (
              <>
                <dt className="font-medium text-sauge">Densité protéique</dt>
                <dd className="font-mono text-craie">
                  {suggestion.protein_density} g / 100 kcal
                </dd>
              </>
            )}
            {suggestion.price_tier !== null && (
              <>
                <dt className="font-medium text-sauge">Prix</dt>
                <dd className="font-mono text-craie">{priceTierLabel(suggestion.price_tier)}</dd>
              </>
            )}
          </dl>

          {(suggestion.allergens ?? []).length > 0 && (
            <p className="mt-4 text-sm text-brique">
              Allergènes : {suggestion.allergens.join(", ")}
            </p>
          )}

          <h3 className="mt-4 font-medium text-craie">Ingrédients</h3>
          <ul className="mt-1 list-disc pl-5 text-sm text-sauge marker:text-lisiere">
            {(suggestion.ingredients ?? []).map((ingredient, index) => (
              <li key={`${ingredient.name}-${index}`}>
                {ingredient.name}
                {ingredient.quantity ? ` — ${ingredient.quantity}` : ""}
              </li>
            ))}
          </ul>

          {(suggestion.instructions ?? []).length > 0 && (
            <>
              <h3 className="mt-4 font-medium text-craie">Préparation</h3>
              <ol className="mt-1 list-decimal pl-5 text-sm text-sauge marker:text-lisiere">
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
