export interface RecipeSuggestion {
  id: number;
  title: string;
  ingredients: string[];
  score: number;
}

export interface SuggestionResponse {
  suggestions: RecipeSuggestion[];
}
