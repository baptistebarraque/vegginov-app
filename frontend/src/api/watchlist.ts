import type { WatchlistEntry } from "../types/watchlist";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface WatchlistEntryResponseBody {
  recipe_id: number;
  title: string;
  image_url: string | null;
  notes: string | null;
  planned_for: string | null;
}

function toEntry(body: WatchlistEntryResponseBody): WatchlistEntry {
  return {
    recipeId: body.recipe_id,
    title: body.title,
    imageUrl: body.image_url,
    notes: body.notes,
    plannedFor: body.planned_for,
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

export async function getWatchlist(): Promise<WatchlistEntry[]> {
  const response = await fetch(`${API_BASE_URL}/watchlist`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Get watchlist request failed: ${response.status}`));
  }

  const body = (await response.json()) as { entries: WatchlistEntryResponseBody[] };
  return body.entries.map(toEntry);
}

export async function addToWatchlist(recipeId: number): Promise<WatchlistEntry> {
  const response = await fetch(`${API_BASE_URL}/watchlist/${recipeId}`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Add to watchlist request failed: ${response.status}`));
  }

  return toEntry((await response.json()) as WatchlistEntryResponseBody);
}

export async function removeFromWatchlist(recipeId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/watchlist/${recipeId}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Remove from watchlist request failed: ${response.status}`));
  }
}

export async function updateWatchlistEntry(
  recipeId: number,
  updates: { notes: string | null; plannedFor: string | null },
): Promise<WatchlistEntry> {
  const response = await fetch(`${API_BASE_URL}/watchlist/${recipeId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ notes: updates.notes, planned_for: updates.plannedFor }),
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Update watchlist entry request failed: ${response.status}`));
  }

  return toEntry((await response.json()) as WatchlistEntryResponseBody);
}
