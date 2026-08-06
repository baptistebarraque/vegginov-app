// Returned by POST/DELETE /likes/{id}: the authoritative state after a toggle.
export interface LikeStatus {
  recipeId: number;
  likeCount: number;
  isLiked: boolean;
}

// An entry in the "Mes coups de cœur" list (GET /likes).
export interface LikedRecipe {
  recipeId: number;
  title: string;
  imageUrl: string | null;
  likeCount: number;
}
