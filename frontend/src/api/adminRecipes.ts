import type { CreatedRecipe } from "../types/recipe";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function createRecipe(
  title: string,
  ingredients: string[],
  allergens: string[],
  prepTimeMinutes: number | null,
): Promise<CreatedRecipe> {
  const response = await fetch(`${API_BASE_URL}/admin/recipes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      title,
      ingredients,
      allergens,
      prep_time_minutes: prepTimeMinutes,
    }),
  });

  if (!response.ok) {
    throw new Error(`Create recipe request failed: ${response.status}`);
  }

  return response.json() as Promise<CreatedRecipe>;
}
