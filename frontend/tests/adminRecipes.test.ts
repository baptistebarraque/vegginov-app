import { afterEach, describe, expect, it, vi } from "vitest";
import {
  CsvImportValidationError,
  createRecipe,
  deleteRecipe,
  exportRecipesCsv,
  getRecipe,
  importRecipesCsv,
  listRecipes,
  updateRecipe,
} from "../src/api/adminRecipes";
import type { RecipeFormValues } from "../src/types/recipe";

const baseValues: RecipeFormValues = {
  title: "Salade",
  ingredients: [{ name: "laitue", quantity: null }],
  allergens: [],
  prepTimeMinutes: 10,
  servings: 4,
  proteinSource: null,
  proteinGrams: null,
  caloriesPerPortion: null,
  priceTier: null,
  instructions: [],
  image: null,
};

describe("createRecipe", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("POSTs the recipe fields as multipart form data, with credentials included", async () => {
    const mockResponse = {
      id: 1,
      title: "Salade",
      ingredients: [{ name: "laitue", quantity: null }],
      allergens: [],
      prep_time_minutes: 10,
      servings: 4,
      protein_source: null,
      protein_grams: null,
      instructions: [],
      image_url: null,
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await createRecipe(baseValues);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/admin\/recipes$/);
    expect(init.method).toBe("POST");
    expect(init.credentials).toBe("include");
    const formData = init.body as FormData;
    expect(formData.get("title")).toBe("Salade");
    expect(formData.get("ingredients")).toBe(JSON.stringify([{ name: "laitue", quantity: null }]));
    expect(formData.get("prep_time_minutes")).toBe("10");
    expect(formData.get("servings")).toBe("4");
    expect(formData.get("protein_source")).toBeNull();
    expect(formData.get("protein_grams")).toBeNull();
    expect(formData.get("calories_per_portion")).toBeNull();
    expect(formData.get("price_tier")).toBeNull();
    expect(formData.get("image")).toBeNull();
    expect(result).toEqual(mockResponse);
  });

  it("appends calories_per_portion and price_tier when provided", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: 1 }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await createRecipe({ ...baseValues, caloriesPerPortion: 420, priceTier: 2 });

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const formData = init.body as FormData;
    expect(formData.get("calories_per_portion")).toBe("420");
    expect(formData.get("price_tier")).toBe("2");
  });

  it("attaches the image file when provided", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: 1, image_url: "/media/abc.png" }),
    });
    vi.stubGlobal("fetch", fetchMock);
    const file = new File(["fake-bytes"], "photo.png", { type: "image/png" });

    await createRecipe({ ...baseValues, image: file });

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const formData = init.body as FormData;
    expect(formData.get("image")).toBe(file);
  });

  it("throws when the response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 403, json: () => Promise.resolve({}) }),
    );

    await expect(createRecipe(baseValues)).rejects.toThrow("403");
  });

  it("surfaces the backend's detail message when present", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: () =>
          Promise.resolve({
            detail: "quantité obligatoire pour chaque ingrédient (manquant pour : laitue)",
          }),
      }),
    );

    await expect(createRecipe(baseValues)).rejects.toThrow(
      "quantité obligatoire pour chaque ingrédient (manquant pour : laitue)",
    );
  });
});

describe("importRecipesCsv", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("POSTs the file as multipart form data and returns the created count", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ created_count: 2 }),
    });
    vi.stubGlobal("fetch", fetchMock);
    const file = new File(["title,ingredients\nSalade,laitue\n"], "recipes.csv", {
      type: "text/csv",
    });

    const result = await importRecipesCsv(file);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/admin\/recipes\/import$/);
    expect(init.method).toBe("POST");
    expect(init.credentials).toBe("include");
    const formData = init.body as FormData;
    expect(formData.get("file")).toBe(file);
    expect(result).toEqual({ created_count: 2 });
  });

  it("throws CsvImportValidationError with the row errors on a 400 response", async () => {
    const rowErrors = [{ row: 3, message: "la colonne 'title' est obligatoire" }];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: rowErrors }),
      }),
    );
    const file = new File(["bad"], "recipes.csv", { type: "text/csv" });

    await expect(importRecipesCsv(file)).rejects.toThrow(CsvImportValidationError);
    try {
      await importRecipesCsv(file);
    } catch (err) {
      expect(err).toBeInstanceOf(CsvImportValidationError);
      expect((err as CsvImportValidationError).rowErrors).toEqual(rowErrors);
    }
  });

  it("throws a generic error for non-400 failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 401, json: () => Promise.resolve({}) }),
    );
    const file = new File(["title,ingredients\n"], "recipes.csv", { type: "text/csv" });

    await expect(importRecipesCsv(file)).rejects.toThrow("401");
  });
});

describe("listRecipes", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("GETs the recipe list with credentials included", async () => {
    const mockResponse = [{ id: 1, title: "Salade", image_url: null }];
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(mockResponse) });
    vi.stubGlobal("fetch", fetchMock);

    const result = await listRecipes();

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/admin\/recipes$/);
    expect(init.credentials).toBe("include");
    expect(result).toEqual(mockResponse);
  });

  it("throws when the response is not ok", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 401 }));

    await expect(listRecipes()).rejects.toThrow("401");
  });
});

describe("exportRecipesCsv", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("GETs the export endpoint with credentials and returns the blob", async () => {
    const blob = new Blob(["title,ingredients\nSalade,laitue\n"], { type: "text/csv" });
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, blob: () => Promise.resolve(blob) });
    vi.stubGlobal("fetch", fetchMock);

    const result = await exportRecipesCsv();

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/admin\/recipes\/export$/);
    expect(init.credentials).toBe("include");
    expect(result).toBe(blob);
  });

  it("throws when the response is not ok", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 401 }));

    await expect(exportRecipesCsv()).rejects.toThrow("401");
  });
});

describe("getRecipe", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("GETs the recipe detail by id", async () => {
    const mockResponse = { id: 1, title: "Salade" };
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(mockResponse) });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getRecipe(1);

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/admin\/recipes\/1$/);
    expect(result).toEqual(mockResponse);
  });

  it("throws when the recipe is not found", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 404 }));

    await expect(getRecipe(999)).rejects.toThrow("404");
  });
});

describe("updateRecipe", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("PUTs the recipe fields as multipart form data", async () => {
    const mockResponse = { id: 1, title: "Salade" };
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(mockResponse) });
    vi.stubGlobal("fetch", fetchMock);

    const result = await updateRecipe(1, baseValues, false);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/admin\/recipes\/1$/);
    expect(init.method).toBe("PUT");
    expect(init.credentials).toBe("include");
    const formData = init.body as FormData;
    expect(formData.get("title")).toBe("Salade");
    expect(formData.get("remove_image")).toBeNull();
    expect(result).toEqual(mockResponse);
  });

  it("includes remove_image when requested", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) });
    vi.stubGlobal("fetch", fetchMock);

    await updateRecipe(1, baseValues, true);

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    const formData = init.body as FormData;
    expect(formData.get("remove_image")).toBe("true");
  });

  it("surfaces the backend's detail message when present", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: "quantité obligatoire pour chaque ingrédient" }),
      }),
    );

    await expect(updateRecipe(1, baseValues, false)).rejects.toThrow(
      "quantité obligatoire pour chaque ingrédient",
    );
  });
});

describe("deleteRecipe", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("DELETEs the recipe by id", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetchMock);

    await deleteRecipe(1);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/admin\/recipes\/1$/);
    expect(init.method).toBe("DELETE");
    expect(init.credentials).toBe("include");
  });

  it("throws when the response is not ok", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 403 }));

    await expect(deleteRecipe(1)).rejects.toThrow("403");
  });
});
