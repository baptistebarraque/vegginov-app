import type { Preferences } from "../types/preference";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface PreferenceResponseBody {
  calorie_orientation: string | null;
  diet: string | null;
  allergens: string[];
  price_range: number | null;
}

function toPreferences(body: PreferenceResponseBody): Preferences {
  return {
    calorieOrientation: body.calorie_orientation as Preferences["calorieOrientation"],
    diet: body.diet as Preferences["diet"],
    allergens: body.allergens,
    priceRange: body.price_range,
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

export async function getPreferences(): Promise<Preferences> {
  const response = await fetch(`${API_BASE_URL}/preferences`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Get preferences request failed: ${response.status}`));
  }

  return toPreferences((await response.json()) as PreferenceResponseBody);
}

export async function updatePreferences(preferences: Preferences): Promise<Preferences> {
  const response = await fetch(`${API_BASE_URL}/preferences`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      calorie_orientation: preferences.calorieOrientation,
      diet: preferences.diet,
      allergens: preferences.allergens,
      price_range: preferences.priceRange,
    }),
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Update preferences request failed: ${response.status}`));
  }

  return toPreferences((await response.json()) as PreferenceResponseBody);
}
