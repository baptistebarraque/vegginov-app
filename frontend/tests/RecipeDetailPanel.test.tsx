import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import RecipeDetailPanel from "../src/components/RecipeDetailPanel";
import type { RecipeSuggestion } from "../src/types/recipe";

function buildSuggestion(overrides: Partial<RecipeSuggestion> = {}): RecipeSuggestion {
  return {
    id: 1,
    title: "Curry de lentilles",
    ingredients: [
      { name: "lentilles corail", quantity: "200g" },
      { name: "lait de coco", quantity: null },
    ],
    score: 0.87,
    allergens: [],
    prep_time_minutes: 25,
    servings: 4,
    protein_source: null,
    protein_grams: null,
    instructions: [],
    image_url: null,
    ...overrides,
  };
}

describe("RecipeDetailPanel", () => {
  it("renders the title, proximity score, and ingredients from props", () => {
    render(<RecipeDetailPanel suggestion={buildSuggestion()} onClose={vi.fn()} />);

    expect(screen.getByRole("heading", { name: "Curry de lentilles" })).toBeInTheDocument();
    expect(screen.getByText("87 % de proximité")).toBeInTheDocument();
    expect(screen.getByText(/lentilles corail/)).toBeInTheDocument();
    expect(screen.getByText(/lait de coco/)).toBeInTheDocument();
  });
});
