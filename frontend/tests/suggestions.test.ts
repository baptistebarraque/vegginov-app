import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchSuggestions } from "../src/api/suggestions";

describe("fetchSuggestions", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("POSTs the title/ingredients with credentials included and ignore_preferences false by default", async () => {
    const mockResponse = { suggestions: [{ id: 1, title: "Curry", ingredients: [], score: 1 }] };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchSuggestions("Poulet au curry", ["poulet", "curry"]);

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/suggestions$/),
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: JSON.stringify({
          title: "Poulet au curry",
          ingredients: ["poulet", "curry"],
          ignore_preferences: false,
        }),
      }),
    );
    expect(result).toEqual(mockResponse);
  });

  it("passes ignore_preferences through when set", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ suggestions: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchSuggestions("Curry", [], true);

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/suggestions$/),
      expect.objectContaining({
        body: JSON.stringify({ title: "Curry", ingredients: [], ignore_preferences: true }),
      }),
    );
  });

  it("throws when the response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 500, json: () => Promise.resolve({}) }),
    );

    await expect(fetchSuggestions("Curry", [])).rejects.toThrow("500");
  });
});
