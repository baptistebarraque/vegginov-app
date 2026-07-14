import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import SuggestionList from "../src/components/SuggestionList";
import type { RecipeSuggestion } from "../src/types/recipe";

const suggestion: RecipeSuggestion = {
  id: 1,
  title: "Curry de lentilles",
  ingredients: ["lentilles", "curry"],
  score: 0.42,
};

describe("SuggestionList", () => {
  it("renders nothing when there are no suggestions", () => {
    const { container } = render(<SuggestionList suggestions={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders a suggestion's title and ingredients", () => {
    render(<SuggestionList suggestions={[suggestion]} />);
    expect(screen.getByText("Curry de lentilles")).toBeInTheDocument();
    expect(screen.getByText("lentilles, curry")).toBeInTheDocument();
  });
});
