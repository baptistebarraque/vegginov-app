import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import RecipeForm from "../src/components/RecipeForm";

describe("RecipeForm", () => {
  it("splits and trims comma-separated ingredients on submit", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<RecipeForm onSubmit={onSubmit} isLoading={false} />);

    await user.type(screen.getByLabelText(/nom de la recette/i), "Poulet au curry");
    await user.type(screen.getByLabelText(/ingrédients/i), "poulet, curry ,  lait de coco ,,");
    await user.click(screen.getByRole("button", { name: /trouver des recettes/i }));

    expect(onSubmit).toHaveBeenCalledWith("Poulet au curry", ["poulet", "curry", "lait de coco"]);
  });

  it("disables the submit button while loading", () => {
    render(<RecipeForm onSubmit={vi.fn()} isLoading={true} />);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
