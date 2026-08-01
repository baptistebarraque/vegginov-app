import type { RecipeSuggestion } from "../types/recipe";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface RecipeSuggestionCardProps {
  suggestion: RecipeSuggestion;
  onClick: () => void;
  onMouseEnter?: () => void;
  onFocus?: () => void;
  expanded?: boolean;
  hint?: string;
}

// suggestion.image_url is a background-removed cutout of the dish (see the
// public/ingredients/ photo convention). No card background/border of its
// own — bg matches the page exactly and object-contain never crops — so the
// cutout blends straight into the page instead of reading as a framed photo.
// Recipes without a photo yet fall back to plain title text.
function RecipeSuggestionCard({
  suggestion,
  onClick,
  onMouseEnter,
  onFocus,
  expanded = false,
  hint,
}: RecipeSuggestionCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      onFocus={onFocus}
      aria-expanded={expanded}
      aria-label={`Voir la recette : ${suggestion.title}`}
      className="flex h-full w-full flex-col items-center justify-center gap-1 rounded-lg px-2 text-center focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
    >
      {suggestion.image_url && (
        <img
          src={`${API_BASE_URL}${suggestion.image_url}`}
          alt={suggestion.title}
          className="max-h-[80%] w-auto object-contain"
        />
      )}
      <p className="font-display text-base text-craie">{suggestion.title}</p>
      {hint && <p className="font-mono text-xs text-sauge">{hint}</p>}
    </button>
  );
}

export default RecipeSuggestionCard;
