export interface WatchlistEntry {
  recipeId: number;
  title: string;
  imageUrl: string | null;
  notes: string | null;
  plannedFor: string | null; // ISO date (YYYY-MM-DD), or null
}
