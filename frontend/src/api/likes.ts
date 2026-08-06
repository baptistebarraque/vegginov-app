import type { LikedRecipe, LikeStatus } from "../types/like";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface LikeStatusResponseBody {
  recipe_id: number;
  like_count: number;
  is_liked: boolean;
}

interface LikedRecipeResponseBody {
  recipe_id: number;
  title: string;
  image_url: string | null;
  like_count: number;
}

function toStatus(body: LikeStatusResponseBody): LikeStatus {
  return {
    recipeId: body.recipe_id,
    likeCount: body.like_count,
    isLiked: body.is_liked,
  };
}

function toLikedRecipe(body: LikedRecipeResponseBody): LikedRecipe {
  return {
    recipeId: body.recipe_id,
    title: body.title,
    imageUrl: body.image_url,
    likeCount: body.like_count,
  };
}

async function extractErrorMessage(response: Response, fallback: string): Promise<string> {
  const body: unknown = await response.json().catch(() => null);
  if (body !== null && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") {
      return detail;
    }
  }
  return fallback;
}

export async function getLikes(): Promise<LikedRecipe[]> {
  const response = await fetch(`${API_BASE_URL}/likes`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Get likes request failed: ${response.status}`));
  }

  const body = (await response.json()) as { likes: LikedRecipeResponseBody[] };
  return body.likes.map(toLikedRecipe);
}

export async function likeRecipe(recipeId: number): Promise<LikeStatus> {
  const response = await fetch(`${API_BASE_URL}/likes/${recipeId}`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Like request failed: ${response.status}`));
  }

  return toStatus((await response.json()) as LikeStatusResponseBody);
}

export async function unlikeRecipe(recipeId: number): Promise<LikeStatus> {
  const response = await fetch(`${API_BASE_URL}/likes/${recipeId}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Unlike request failed: ${response.status}`));
  }

  return toStatus((await response.json()) as LikeStatusResponseBody);
}
