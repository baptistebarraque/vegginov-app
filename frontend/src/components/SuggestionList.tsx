import type { RecipeSuggestion } from "../types/recipe";

interface SuggestionListProps {
  suggestions: RecipeSuggestion[];
}

function SuggestionList({ suggestions }: SuggestionListProps) {
  if (suggestions.length === 0) {
    return null;
  }

  return (
    <ul className="flex w-full max-w-md flex-col gap-2">
      {suggestions.map((suggestion) => (
        <li
          key={suggestion.id}
          className="rounded border border-neutral-200 px-3 py-2 text-left dark:border-neutral-700"
        >
          <p className="font-medium text-neutral-900 dark:text-white">{suggestion.title}</p>
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            {suggestion.ingredients.join(", ")}
          </p>
        </li>
      ))}
    </ul>
  );
}

export default SuggestionList;
