import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import RecipeSuggestionGrid from "../src/components/RecipeSuggestionGrid";
import type { RecipeSuggestion } from "../src/types/recipe";

function mockCanHover(matches: boolean) {
  vi.spyOn(window, "matchMedia").mockReturnValue({
    matches,
    media: "",
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}

function buildSuggestion(overrides: Partial<RecipeSuggestion> = {}): RecipeSuggestion {
  return {
    id: 1,
    title: "Curry de lentilles",
    ingredients: [{ name: "lentilles", quantity: "200g" }],
    score: 0.42,
    allergens: [],
    prep_time_minutes: null,
    servings: null,
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

describe("RecipeSuggestionGrid", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders nothing when there are no suggestions", () => {
    const { container } = render(<RecipeSuggestionGrid suggestions={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders a title placeholder when a suggestion has no image", () => {
    render(<RecipeSuggestionGrid suggestions={[buildSuggestion()]} />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getAllByText("Curry de lentilles")).toHaveLength(1);
  });

  it("renders the dish photo as a borderless cutout when a suggestion has one", () => {
    const suggestion = buildSuggestion({ image_url: "/media/abc123.png" });
    render(<RecipeSuggestionGrid suggestions={[suggestion]} />);
    expect(screen.getByRole("img", { name: "Curry de lentilles" })).toBeInTheDocument();
  });

  it("renders one card per suggestion, even fewer than 4", () => {
    const suggestions = [buildSuggestion({ id: 1 }), buildSuggestion({ id: 2, title: "Salade" })];
    render(<RecipeSuggestionGrid suggestions={suggestions} />);
    expect(screen.getAllByText("Salade")).toHaveLength(1);
  });

  it("grows the hovered card's row and column tracks without hiding siblings", () => {
    const suggestions = [
      buildSuggestion({ id: 1, title: "Curry" }),
      buildSuggestion({ id: 2, title: "Salade" }),
      buildSuggestion({ id: 3, title: "Tofu" }),
      buildSuggestion({ id: 4, title: "Chili" }),
    ];
    const { container } = render(<RecipeSuggestionGrid suggestions={suggestions} />);
    const gridContainer = container.firstChild as HTMLElement;

    expect(gridContainer.style.gridTemplateColumns).toBe("1fr 1fr");
    expect(gridContainer.style.gridTemplateRows).toBe("1fr 1fr");

    fireEvent.mouseEnter(screen.getByRole("button", { name: /Curry/ }));
    expect(gridContainer.style.gridTemplateColumns).toBe("3fr 1fr");
    expect(gridContainer.style.gridTemplateRows).toBe("3fr 1fr");
    expect(screen.getAllByRole("button")).toHaveLength(4);

    fireEvent.mouseEnter(screen.getByRole("button", { name: /Chili/ }));
    expect(gridContainer.style.gridTemplateColumns).toBe("1fr 3fr");
    expect(gridContainer.style.gridTemplateRows).toBe("1fr 3fr");
  });

  it("returns to neutral tracks when the mouse leaves the hovered card", () => {
    const { container } = render(<RecipeSuggestionGrid suggestions={[buildSuggestion()]} />);
    const gridContainer = container.firstChild as HTMLElement;

    const card = screen.getByRole("button", { name: /Curry de lentilles/ });
    fireEvent.mouseEnter(card);
    expect(gridContainer.style.gridTemplateColumns).toBe("3fr 1fr");

    fireEvent.mouseLeave(card);
    expect(gridContainer.style.gridTemplateColumns).toBe("1fr 1fr");
    expect(gridContainer.style.gridTemplateRows).toBe("1fr 1fr");
  });

  it("expands on keyboard focus and collapses when focus leaves the grid", () => {
    const suggestions = [
      buildSuggestion({ id: 1, title: "Curry" }),
      buildSuggestion({ id: 2, title: "Salade" }),
    ];
    const { container } = render(<RecipeSuggestionGrid suggestions={suggestions} />);
    const gridContainer = container.firstChild as HTMLElement;
    const card = screen.getByRole("button", { name: /Curry/ });

    fireEvent.focus(card);
    expect(gridContainer.style.gridTemplateColumns).toBe("3fr 1fr");

    fireEvent.blur(card, { relatedTarget: document.body });
    expect(gridContainer.style.gridTemplateColumns).toBe("1fr 1fr");
  });

  it("returns focus to the triggering card when the detail panel closes", async () => {
    const user = userEvent.setup();
    render(<RecipeSuggestionGrid suggestions={[buildSuggestion()]} />);

    const card = screen.getByRole("button", { name: /Curry de lentilles/ });
    await user.click(card);
    await user.click(screen.getByLabelText("Fermer"));

    expect(card).toHaveFocus();
  });

  it("opens the detail panel on click and closes it on Escape", async () => {
    const user = userEvent.setup();
    render(
      <RecipeSuggestionGrid
        suggestions={[
          buildSuggestion({ instructions: ["Faire revenir les oignons"], servings: 4 }),
        ]}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Curry de lentilles/ }));

    expect(screen.getByText("Faire revenir les oignons")).toBeInTheDocument();
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    fireEvent.keyDown(document, { key: "Escape" });

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(screen.queryByText("Faire revenir les oignons")).not.toBeInTheDocument();
  });

  it("closes the detail panel when clicking its close button", async () => {
    const user = userEvent.setup();
    render(<RecipeSuggestionGrid suggestions={[buildSuggestion()]} />);

    await user.click(screen.getByRole("button", { name: /Curry de lentilles/ }));
    await user.click(screen.getByLabelText("Fermer"));

    expect(screen.getByRole("button", { name: /Curry de lentilles/ })).toBeInTheDocument();
  });

  it("on a touch device, a first tap only expands and a second tap opens the detail", () => {
    mockCanHover(false);
    render(
      <RecipeSuggestionGrid
        suggestions={[buildSuggestion({ instructions: ["Faire revenir les oignons"] })]}
      />,
    );

    const card = screen.getByRole("button", { name: /Curry de lentilles/ });
    fireEvent.click(card);

    expect(screen.queryByText("Faire revenir les oignons")).not.toBeInTheDocument();
    expect(screen.getByText("Toucher à nouveau pour voir la recette")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Curry de lentilles/ }));

    expect(screen.getByText("Faire revenir les oignons")).toBeInTheDocument();
  });

  it("on a device that supports hover, a single click opens the detail directly", () => {
    mockCanHover(true);
    render(
      <RecipeSuggestionGrid
        suggestions={[buildSuggestion({ instructions: ["Faire revenir les oignons"] })]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Curry de lentilles/ }));

    expect(screen.getByText("Faire revenir les oignons")).toBeInTheDocument();
  });

  it("calls onToggleLike with the recipe id from the opened detail panel", async () => {
    const user = userEvent.setup();
    const onToggleLike = vi.fn();
    render(
      <RecipeSuggestionGrid
        suggestions={[buildSuggestion({ id: 7, like_count: 2 })]}
        onToggleLike={onToggleLike}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Curry de lentilles/ }));
    await user.click(screen.getByRole("button", { name: /Aimer cette recette/ }));

    expect(onToggleLike).toHaveBeenCalledWith(7);
  });

  it("closes the detail panel when clicking the backdrop", async () => {
    const user = userEvent.setup();
    const { container } = render(<RecipeSuggestionGrid suggestions={[buildSuggestion()]} />);

    await user.click(screen.getByRole("button", { name: /Curry de lentilles/ }));
    const backdrop = container.querySelector(".fixed.inset-0");
    expect(backdrop).not.toBeNull();
    await user.click(backdrop as Element);

    expect(screen.getByRole("button", { name: /Curry de lentilles/ })).toBeInTheDocument();
  });
});
