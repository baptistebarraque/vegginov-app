import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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
    calories_per_portion: null,
    price_tier: null,
    protein_density: null,
    instructions: [],
    image_url: null,
    is_watchlisted: false,
    is_liked: false,
    like_count: 0,
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

  it("renders per-portion calories, protein density, and the price tier when present", () => {
    render(
      <RecipeDetailPanel
        suggestion={buildSuggestion({
          protein_grams: 20,
          calories_per_portion: 200,
          protein_density: 10,
          price_tier: 2,
        })}
        onClose={vi.fn()}
      />,
    );

    expect(screen.getByText("20 g")).toBeInTheDocument();
    expect(screen.getByText("200 kcal")).toBeInTheDocument();
    expect(screen.getByText("10 g / 100 kcal")).toBeInTheDocument();
    expect(screen.getByText("€€")).toBeInTheDocument();
  });

  it("omits the nutrition rows when the values are absent", () => {
    render(<RecipeDetailPanel suggestion={buildSuggestion()} onClose={vi.fn()} />);

    expect(screen.queryByText(/kcal/)).not.toBeInTheDocument();
    expect(screen.queryByText(/100 kcal/)).not.toBeInTheDocument();
    expect(screen.queryByText("Prix")).not.toBeInTheDocument();
  });

  it("shows the like count and reflects the liked state when onToggleLike is given", () => {
    render(
      <RecipeDetailPanel
        suggestion={buildSuggestion({ is_liked: true, like_count: 3 })}
        onClose={vi.fn()}
        onToggleLike={vi.fn()}
      />,
    );

    const likeButton = screen.getByRole("button", { name: /Ne plus aimer cette recette/ });
    expect(likeButton).toHaveAttribute("aria-pressed", "true");
    expect(likeButton).toHaveTextContent("3");
  });

  it("calls onToggleLike when the heart is clicked", async () => {
    const onToggleLike = vi.fn();
    render(
      <RecipeDetailPanel
        suggestion={buildSuggestion()}
        onClose={vi.fn()}
        onToggleLike={onToggleLike}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: /Aimer cette recette/ }));

    expect(onToggleLike).toHaveBeenCalledOnce();
  });

  it("renders no like button when onToggleLike is omitted", () => {
    render(<RecipeDetailPanel suggestion={buildSuggestion({ like_count: 3 })} onClose={vi.fn()} />);

    expect(screen.queryByRole("button", { name: /aimer cette recette/i })).not.toBeInTheDocument();
  });
});
