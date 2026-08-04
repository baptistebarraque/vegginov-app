import type { SuggestionResponse } from "../types/recipe";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function fetchSuggestions(
  title: string,
  ingredients: string[],
  ignorePreferences = false,
): Promise<SuggestionResponse> {
  const response = await fetch(`${API_BASE_URL}/suggestions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    // Included so a logged-in user's session cookie reaches the backend —
    // /suggestions applies their allergen preferences when present, but
    // works anonymously too (accounts are optional).
    credentials: "include",
    body: JSON.stringify({ title, ingredients, ignore_preferences: ignorePreferences }),
  });

  if (!response.ok) {
    throw new Error(`Suggestion request failed: ${response.status}`);
  }

  return response.json() as Promise<SuggestionResponse>;
}
