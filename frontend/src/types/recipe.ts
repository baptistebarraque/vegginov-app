export interface RecipeSuggestion {
  id: number;
  title: string;
  ingredients: string[];
  score: number;
}

export interface SuggestionResponse {
  suggestions: RecipeSuggestion[];
}

export interface CreatedRecipe {
  id: number;
  title: string;
  ingredients: string[];
  allergens: string[];
  prep_time_minutes: number | null;
}
