export type CalorieOrientation = "low" | "balanced" | "high";
export type Diet = "omnivore" | "vegetarian" | "pescatarian" | "vegan";

export interface Preferences {
  calorieOrientation: CalorieOrientation | null;
  diet: Diet | null;
  allergens: string[];
  priceRange: number | null;
}
