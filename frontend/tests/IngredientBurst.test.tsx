import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import IngredientBurst from "../src/components/IngredientBurst";
import type { IngredientEntry } from "../src/types/recipe";

function entry(name: string): IngredientEntry {
  return { name, quantity: null };
}

// jsdom has no layout engine, so these tests can only assert the cut-outs are
// present, decorative and pointing at the right files — not that they end up
// visually on-screen. The scatter/occlusion has to be eyeballed in a browser.
describe("IngredientBurst", () => {
  it("renders one decorative cut-out per matched ingredient", () => {
    const { container } = render(
      <IngredientBurst ingredients={[entry("1 oignon émincé"), entry("2 tomates")]} />,
    );

    const images = container.querySelectorAll("img");
    expect(images).toHaveLength(2);
    expect(images[0]).toHaveAttribute("src", "/ingredients/onion.png");
    expect(images[1]).toHaveAttribute("src", "/ingredients/tomato.png");
    // Decorative only: the accessible ingredient list lives in the panel text.
    expect(images[0]).toHaveAttribute("alt", "");
    expect(container.firstChild).toHaveAttribute("aria-hidden", "true");
  });

  it("caps the burst at six cut-outs even with more matching ingredients", () => {
    const { container } = render(
      <IngredientBurst
        ingredients={[
          entry("tomate"),
          entry("oignon"),
          entry("ail"),
          entry("tofu"),
          entry("courgette"),
          entry("aubergine"),
          entry("carotte"),
          entry("brocoli"),
        ]}
      />,
    );

    expect(container.querySelectorAll("img")).toHaveLength(6);
  });

  it("renders nothing when no ingredient has a matching photo", () => {
    const { container } = render(
      <IngredientBurst ingredients={[entry("Herbes de Provence"), entry("Sel")]} />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});
