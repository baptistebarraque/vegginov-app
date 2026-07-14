import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchSuggestions } from "../src/api/suggestions";

describe("fetchSuggestions", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("POSTs the title and ingredients and returns the parsed response", async () => {
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
        body: JSON.stringify({ title: "Poulet au curry", ingredients: ["poulet", "curry"] }),
      }),
    );
    expect(result).toEqual(mockResponse);
  });

  it("throws when the response is not ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 500, json: () => Promise.resolve({}) }),
    );

    await expect(fetchSuggestions("Curry", [])).rejects.toThrow("500");
  });
});
