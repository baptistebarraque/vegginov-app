import type {
  AdminUserDetail,
  AdminUserListItem,
  AdminUserPreferences,
  AdminUserRecipeRef,
  AdminUserWatchlistItem,
} from "../types/adminUser";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface AdminUserListItemBody {
  id: number;
  email: string;
  is_admin: boolean;
  created_at: string;
  watchlist_count: number;
  like_count: number;
  has_preferences: boolean;
}

interface AdminUserRecipeRefBody {
  recipe_id: number;
  title: string;
  image_url: string | null;
}

interface AdminUserWatchlistItemBody extends AdminUserRecipeRefBody {
  notes: string | null;
  planned_for: string | null;
}

interface AdminUserPreferencesBody {
  calorie_orientation: string | null;
  diet: string | null;
  allergens: string[];
  price_range: number | null;
}

interface AdminUserDetailBody extends AdminUserListItemBody {
  preferences: AdminUserPreferencesBody | null;
  watchlist: AdminUserWatchlistItemBody[];
  likes: AdminUserRecipeRefBody[];
}

function toListItem(body: AdminUserListItemBody): AdminUserListItem {
  return {
    id: body.id,
    email: body.email,
    isAdmin: body.is_admin,
    createdAt: body.created_at,
    watchlistCount: body.watchlist_count,
    likeCount: body.like_count,
    hasPreferences: body.has_preferences,
  };
}

function toRecipeRef(body: AdminUserRecipeRefBody): AdminUserRecipeRef {
  return { recipeId: body.recipe_id, title: body.title, imageUrl: body.image_url };
}

function toWatchlistItem(body: AdminUserWatchlistItemBody): AdminUserWatchlistItem {
  return { ...toRecipeRef(body), notes: body.notes, plannedFor: body.planned_for };
}

// Same cast as api/preferences.ts: the backend validates these against its own
// vocabularies (CALORIE_ORIENTATIONS / DIETS), so the wire strings are narrowed
// here rather than re-validated.
function toPreferences(body: AdminUserPreferencesBody): AdminUserPreferences {
  return {
    calorieOrientation: body.calorie_orientation as AdminUserPreferences["calorieOrientation"],
    diet: body.diet as AdminUserPreferences["diet"],
    allergens: body.allergens,
    priceRange: body.price_range,
  };
}

function toDetail(body: AdminUserDetailBody): AdminUserDetail {
  return {
    ...toListItem(body),
    preferences: body.preferences === null ? null : toPreferences(body.preferences),
    watchlist: body.watchlist.map(toWatchlistItem),
    likes: body.likes.map(toRecipeRef),
  };
}

export async function listUsers(): Promise<AdminUserListItem[]> {
  const response = await fetch(`${API_BASE_URL}/admin/users`, { credentials: "include" });

  if (!response.ok) {
    throw new Error(`List users request failed: ${response.status}`);
  }

  return ((await response.json()) as AdminUserListItemBody[]).map(toListItem);
}

export async function getUser(id: number): Promise<AdminUserDetail> {
  const response = await fetch(`${API_BASE_URL}/admin/users/${id}`, { credentials: "include" });

  if (!response.ok) {
    throw new Error(`Get user request failed: ${response.status}`);
  }

  return toDetail((await response.json()) as AdminUserDetailBody);
}
