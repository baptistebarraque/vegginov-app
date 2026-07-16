import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import AdminRecipeForm from "../src/components/AdminRecipeForm";

describe("AdminRecipeForm", () => {
  it("splits/trims ingredients and allergens, and parses prep time as a number", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<AdminRecipeForm onSubmit={onSubmit} isLoading={false} />);

    await user.type(screen.getByLabelText(/nom de la recette/i), "Curry de lentilles corail");
    await user.type(
      screen.getByLabelText(/ingrédients/i),
      "lentilles corail, lait de coco ,  curry ,,",
    );
    await user.type(screen.getByLabelText(/allergènes/i), "gluten,  lactose");
    await user.type(screen.getByLabelText(/temps de préparation/i), "25");
    await user.click(screen.getByRole("button", { name: /ajouter la recette/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      "Curry de lentilles corail",
      ["lentilles corail", "lait de coco", "curry"],
      ["gluten", "lactose"],
      25,
    );
  });

  it("submits empty allergens and null prep time when those optional fields are left blank", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<AdminRecipeForm onSubmit={onSubmit} isLoading={false} />);

    await user.type(screen.getByLabelText(/nom de la recette/i), "Salade");
    await user.type(screen.getByLabelText(/ingrédients/i), "laitue");
    await user.click(screen.getByRole("button", { name: /ajouter la recette/i }));

    expect(onSubmit).toHaveBeenCalledWith("Salade", ["laitue"], [], null);
  });

  it("disables the submit button while loading", () => {
    render(<AdminRecipeForm onSubmit={vi.fn()} isLoading={true} />);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});
