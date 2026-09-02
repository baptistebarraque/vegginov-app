import type { CalorieOrientation, Diet } from "./preference";

export interface AdminUserListItem {
  id: number;
  email: string;
  isAdmin: boolean;
  createdAt: string; // ISO datetime
  watchlistCount: number;
  likeCount: number;
  hasPreferences: boolean;
}

export interface AdminUserPreferences {
  calorieOrientation: CalorieOrientation | null;
  diet: Diet | null;
  allergens: string[];
  priceRange: number | null;
}

export interface AdminUserRecipeRef {
  recipeId: number;
  title: string;
  imageUrl: string | null;
}

export interface AdminUserWatchlistItem extends AdminUserRecipeRef {
  notes: string | null;
  plannedFor: string | null; // ISO date (YYYY-MM-DD), or null
}

export interface AdminUserDetail extends AdminUserListItem {
  // null when the account never saved a preference profile — preferences are
  // created lazily on first save, so "none" is a normal state.
  preferences: AdminUserPreferences | null;
  watchlist: AdminUserWatchlistItem[];
  likes: AdminUserRecipeRef[];
}
