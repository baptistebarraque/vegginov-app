import { describe, expect, it } from "vitest";
import { matchIngredientImages } from "../src/utils/ingredientImages";
import type { IngredientEntry } from "../src/types/recipe";

function entry(name: string): IngredientEntry {
  return { name, quantity: null };
}

describe("matchIngredientImages", () => {
  it("matches ingredients against known keys, ignoring case, accents and plurals", () => {
    const matches = matchIngredientImages([
      entry("2 gousses d'ail émincées"),
      entry("Tomates cerises"),
      entry("400 g de tofu ferme"),
    ]);

    expect(matches.map((match) => match.key)).toEqual(["garlic", "tomato", "tofu"]);
    expect(matches[0].imageUrl).toBe("/ingredients/garlic.png");
  });

  it("omits ingredients with no recognized photo instead of using a fallback", () => {
    const matches = matchIngredientImages([entry("Herbes de Provence"), entry("Tofu")]);

    expect(matches.map((match) => match.key)).toEqual(["tofu"]);
  });

  it("prefers the more specific keyword over a generic one sharing the same root", () => {
    expect(matchIngredientImages([entry("1/2 oignon rouge émincé")]).map((m) => m.key)).toEqual([
      "red-onion",
    ]);
    expect(matchIngredientImages([entry("1 oignon émincé")]).map((m) => m.key)).toEqual(["onion"]);
    expect(matchIngredientImages([entry("300 g de nouilles de riz")]).map((m) => m.key)).toEqual([
      "rice-noodles",
    ]);
    expect(matchIngredientImages([entry("320 g de riz arborio")]).map((m) => m.key)).toEqual([
      "rice",
    ]);
    expect(matchIngredientImages([entry("2 patates douces coupées en cubes")]).map((m) => m.key)).toEqual([
      "sweet-potato",
    ]);
    expect(matchIngredientImages([entry("3 pommes de terre en cubes")]).map((m) => m.key)).toEqual([
      "potato",
    ]);
  });

  it("does not match a short keyword inside an unrelated longer word", () => {
    expect(matchIngredientImages([entry("Pâte à pizza")])).toEqual([]);
  });

  it("deduplicates repeated ingredients that map to the same key", () => {
    const matches = matchIngredientImages([entry("2 tomates"), entry("Tomates cerises")]);
    expect(matches).toHaveLength(1);
  });

  it("caps the number of matches at maxCount", () => {
    const matches = matchIngredientImages(
      [entry("tomate"), entry("oignon"), entry("ail"), entry("tofu")],
      2,
    );
    expect(matches).toHaveLength(2);
  });

  it("returns an empty list for an empty ingredient list", () => {
    expect(matchIngredientImages([])).toEqual([]);
  });
});
