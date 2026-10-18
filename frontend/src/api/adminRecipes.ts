import type {
  CsvImportResult,
  DishStructureOptions,
  RecipeDetail,
  RecipeFormValues,
  RecipeListItem,
} from "../types/recipe";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function buildRecipeFormData(values: RecipeFormValues): FormData {
  const formData = new FormData();
  formData.append("title", values.title);
  // Ingredients travel as one JSON-encoded field, not repeated form fields:
  // each entry is a {name, quantity} pair, which multipart's flat key-value
  // fields can't express as a plain repeated list the way allergens/
  // instructions do.
  formData.append("ingredients", JSON.stringify(values.ingredients));
  for (const allergen of values.allergens) formData.append("allergens", allergen);
  for (const step of values.instructions) formData.append("instructions", step);
  if (values.prepTimeMinutes !== null) {
    formData.append("prep_time_minutes", String(values.prepTimeMinutes));
  }
  if (values.servings !== null) {
    formData.append("servings", String(values.servings));
  }
  if (values.proteinSource !== null) {
    formData.append("protein_source", values.proteinSource);
  }
  if (values.proteinGrams !== null) {
    formData.append("protein_grams", String(values.proteinGrams));
  }
  if (values.caloriesPerPortion !== null) {
    formData.append("calories_per_portion", String(values.caloriesPerPortion));
  }
  if (values.priceTier !== null) {
    formData.append("price_tier", String(values.priceTier));
  }
  // Always sent, like allergens: saving a recipe rewrites every field, so
  // an absent list would erase the recipe's tags.
  for (const dishType of values.dishTypes) formData.append("dish_types", dishType);
  if (values.cuisine !== null) {
    formData.append("cuisine", values.cuisine);
  }
  if (values.image !== null) {
    formData.append("image", values.image);
  }
  return formData;
}

// The backend returns a plain-string `detail` for most 400s (invalid image,
// malformed ingredients, missing quantities...) — surface it instead of a
// generic message so the admin knows what to fix.
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

export async function createRecipe(values: RecipeFormValues): Promise<RecipeDetail> {
  // No explicit Content-Type header: the browser sets the multipart
  // boundary itself when the body is a FormData instance.
  const response = await fetch(`${API_BASE_URL}/admin/recipes`, {
    method: "POST",
    credentials: "include",
    body: buildRecipeFormData(values),
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Create recipe request failed: ${response.status}`));
  }

  return response.json() as Promise<RecipeDetail>;
}

export async function getProteinSourceOptions(): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/admin/protein-sources`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`List protein source options request failed: ${response.status}`);
  }

  return response.json() as Promise<string[]>;
}

export async function getDishStructureOptions(): Promise<DishStructureOptions> {
  const response = await fetch(`${API_BASE_URL}/admin/dish-structure-options`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`List dish structure options request failed: ${response.status}`);
  }

  return response.json() as Promise<DishStructureOptions>;
}

export async function listRecipes(): Promise<RecipeListItem[]> {
  const response = await fetch(`${API_BASE_URL}/admin/recipes`, { credentials: "include" });

  if (!response.ok) {
    throw new Error(`List recipes request failed: ${response.status}`);
  }

  return response.json() as Promise<RecipeListItem[]>;
}

export async function getRecipe(id: number): Promise<RecipeDetail> {
  const response = await fetch(`${API_BASE_URL}/admin/recipes/${id}`, { credentials: "include" });

  if (!response.ok) {
    throw new Error(`Get recipe request failed: ${response.status}`);
  }

  return response.json() as Promise<RecipeDetail>;
}

export async function updateRecipe(
  id: number,
  values: RecipeFormValues,
  removeImage: boolean,
): Promise<RecipeDetail> {
  const formData = buildRecipeFormData(values);
  if (removeImage) {
    formData.append("remove_image", "true");
  }

  const response = await fetch(`${API_BASE_URL}/admin/recipes/${id}`, {
    method: "PUT",
    credentials: "include",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, `Update recipe request failed: ${response.status}`));
  }

  return response.json() as Promise<RecipeDetail>;
}

export async function deleteRecipe(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/admin/recipes/${id}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Delete recipe request failed: ${response.status}`);
  }
}

// Fetched (rather than a plain <a download>) so the session cookie is sent
// with the request even though the API is on a different origin; returns the
// CSV as a Blob the caller can turn into a download.
export async function exportRecipesCsv(): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/admin/recipes/export`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Export CSV request failed: ${response.status}`);
  }

  return response.blob();
}

// Thrown when the backend rejects a CSV import for row-level reasons (a
// 400 with a { row, message }[] detail) — distinct from a generic network/
// server error, so the UI can render a per-row error list.
export class CsvImportValidationError extends Error {
  readonly rowErrors: { row: number; message: string }[];

  constructor(rowErrors: { row: number; message: string }[]) {
    super("CSV import validation failed");
    this.name = "CsvImportValidationError";
    this.rowErrors = rowErrors;
  }
}

export async function importRecipesCsv(file: File): Promise<CsvImportResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/admin/recipes/import`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });

  if (!response.ok) {
    if (response.status === 400) {
      const body: unknown = await response.json();
      if (
        typeof body === "object" &&
        body !== null &&
        "detail" in body &&
        Array.isArray((body as { detail: unknown }).detail)
      ) {
        throw new CsvImportValidationError(
          (body as { detail: { row: number; message: string }[] }).detail,
        );
      }
    }
    throw new Error(`Import CSV request failed: ${response.status}`);
  }

  return response.json() as Promise<CsvImportResult>;
}
