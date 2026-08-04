export interface RecipeSuggestion {
  id: number;
  title: string;
  ingredients: IngredientEntry[];
  score: number;
  allergens: string[];
  prep_time_minutes: number | null;
  servings: number | null;
  protein_source: string | null;
  protein_grams: number | null;
  calories_per_portion: number | null;
  price_tier: number | null;
  protein_density: number | null; // grams of protein per 100 kcal, computed by the backend
  instructions: string[];
  image_url: string | null;
  is_watchlisted: boolean;
}

export interface SuggestionResponse {
  suggestions: RecipeSuggestion[];
}

export interface IngredientEntry {
  name: string;
  quantity: string | null;
}

export interface RecipeDetail {
  id: number;
  title: string;
  ingredients: IngredientEntry[];
  allergens: string[];
  prep_time_minutes: number | null;
  servings: number | null;
  protein_source: string | null;
  protein_grams: number | null;
  calories_per_portion: number | null;
  price_tier: number | null;
  protein_density: number | null; // grams of protein per 100 kcal, computed by the backend
  instructions: string[];
  image_url: string | null;
}

export interface RecipeListItem {
  id: number;
  title: string;
  image_url: string | null;
}

export interface RecipeFormValues {
  title: string;
  ingredients: IngredientEntry[];
  allergens: string[];
  prepTimeMinutes: number | null;
  servings: number | null;
  proteinSource: string | null;
  proteinGrams: number | null;
  caloriesPerPortion: number | null;
  priceTier: number | null;
  instructions: string[];
  image: File | null;
}

export interface CsvImportRowError {
  row: number;
  message: string;
}

export interface CsvImportResult {
  created_count: number;
}
