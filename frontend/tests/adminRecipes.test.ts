import { afterEach, describe, expect, it, vi } from "vitest";
import { createRecipe } from "../src/api/adminRecipes";

describe("createRecipe", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("POSTs the recipe fields (snake_case prep_time_minutes) with credentials included", async () => {
    const mockResponse = {
      id: 1,
      title: "Salade",
      ingredients: ["laitue"],
      allergens: [],
      prep_time_minutes: 10,
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await createRecipe("Salade", ["laitue"], [], 10);

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/admin\/recipes$/),
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          title: "Salade",
          ingredients: ["laitue"],
          allergens: [],
          prep_time_minutes: 10,
        }),
      }),
    );
    expect(result).toEqual(mockResponse);
  });

  it("throws when the response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 403, json: () => Promise.resolve({}) }),
    );

    await expect(createRecipe("Salade", ["laitue"], [], null)).rejects.toThrow("403");
  });
});
