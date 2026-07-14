import type { SuggestionResponse } from "../types/recipe";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function fetchSuggestions(
  title: string,
  ingredients: string[],
): Promise<SuggestionResponse> {
  const response = await fetch(`${API_BASE_URL}/suggestions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, ingredients }),
  });

  if (!response.ok) {
    throw new Error(`Suggestion request failed: ${response.status}`);
  }

  return response.json() as Promise<SuggestionResponse>;
}
