import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import AdminRecipeForm from "../src/components/AdminRecipeForm";
import type { RecipeFormValues } from "../src/types/recipe";

describe("AdminRecipeForm", () => {
  it("submits multiple ingredients with name+quantity, allergens, instructions and numeric fields", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<AdminRecipeForm onSubmit={onSubmit} isLoading={false} />);

    await user.type(screen.getByLabelText(/nom de la recette/i), "Curry de lentilles corail");
    await user.type(screen.getByLabelText(/nom de l'ingrédient 1/i), "lentilles corail");
    await user.type(screen.getByLabelText(/quantité de l'ingrédient 1/i), "200g");
    await user.click(screen.getByRole("button", { name: /ajouter un ingrédient/i }));
    await user.type(screen.getByLabelText(/nom de l'ingrédient 2/i), "curry");
    await user.type(screen.getByLabelText(/quantité de l'ingrédient 2/i), "1 c.a.s");
    await user.type(screen.getByLabelText(/allergènes/i), "gluten,  lactose");
    await user.type(screen.getByLabelText(/temps de préparation/i), "25");
    await user.type(screen.getByLabelText(/nombre de personnes/i), "4");
    await user.type(screen.getByLabelText(/source de protéines/i), "lentilles corail");
    await user.type(screen.getByLabelText(/protéines en grammes/i), "18.5");
    await user.type(
      screen.getByLabelText(/étapes de préparation/i),
      "Faire revenir les oignons{enter}{enter}Ajouter les lentilles et le curry",
    );
    await user.click(screen.getByRole("button", { name: /ajouter la recette/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      {
        title: "Curry de lentilles corail",
        ingredients: [
          { name: "lentilles corail", quantity: "200g" },
          { name: "curry", quantity: "1 c.a.s" },
        ],
        allergens: ["gluten", "lactose"],
        prepTimeMinutes: 25,
        servings: 4,
        proteinSource: "lentilles corail",
        proteinGrams: 18.5,
        instructions: ["Faire revenir les oignons", "Ajouter les lentilles et le curry"],
        image: null,
      },
      false,
    );
  });

  it("includes the selected image file", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<AdminRecipeForm onSubmit={onSubmit} isLoading={false} />);
    const file = new File(["fake-bytes"], "photo.png", { type: "image/png" });

    await user.type(screen.getByLabelText(/nom de la recette/i), "Salade");
    await user.type(screen.getByLabelText(/nom de l'ingrédient 1/i), "laitue");
    await user.upload(screen.getByLabelText(/photo de la recette/i), file);
    await user.click(screen.getByRole("button", { name: /ajouter la recette/i }));

    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ image: file }), false);
  });

  it("submits null quantity and empty/null optional fields when left blank", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<AdminRecipeForm onSubmit={onSubmit} isLoading={false} />);

    await user.type(screen.getByLabelText(/nom de la recette/i), "Salade");
    await user.type(screen.getByLabelText(/nom de l'ingrédient 1/i), "laitue");
    await user.click(screen.getByRole("button", { name: /ajouter la recette/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      {
        title: "Salade",
        ingredients: [{ name: "laitue", quantity: null }],
        allergens: [],
        prepTimeMinutes: null,
        servings: null,
        proteinSource: null,
        proteinGrams: null,
        instructions: [],
        image: null,
      },
      false,
    );
  });

  it("drops ingredient rows left with an empty name", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(<AdminRecipeForm onSubmit={onSubmit} isLoading={false} />);

    await user.type(screen.getByLabelText(/nom de la recette/i), "Salade");
    await user.type(screen.getByLabelText(/nom de l'ingrédient 1/i), "laitue");
    await user.click(screen.getByRole("button", { name: /ajouter un ingrédient/i }));
    // second row's name is left blank
    await user.click(screen.getByRole("button", { name: /ajouter la recette/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ ingredients: [{ name: "laitue", quantity: null }] }),
      false,
    );
  });

  it("shows a quantity-required hint once a number of people is entered", async () => {
    const user = userEvent.setup();
    render(<AdminRecipeForm onSubmit={vi.fn()} isLoading={false} />);

    expect(screen.queryByText(/quantité obligatoire/i)).not.toBeInTheDocument();

    await user.type(screen.getByLabelText(/nombre de personnes/i), "4");

    expect(screen.getByText(/quantité obligatoire/i)).toBeInTheDocument();
  });

  it("disables the submit button while loading", () => {
    render(<AdminRecipeForm onSubmit={vi.fn()} isLoading={true} />);
    expect(screen.getByRole("button", { name: "Ajout..." })).toBeDisabled();
  });

  const editInitialValues: RecipeFormValues = {
    title: "Curry de lentilles",
    ingredients: [{ name: "lentilles", quantity: "200g" }],
    allergens: ["gluten"],
    prepTimeMinutes: 25,
    servings: 4,
    proteinSource: "lentilles",
    proteinGrams: 18.5,
    instructions: ["Étape 1"],
    image: null,
  };

  it("prefills fields from initialValues and uses custom submit label", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(
      <AdminRecipeForm
        onSubmit={onSubmit}
        isLoading={false}
        initialValues={editInitialValues}
        submitLabel="Enregistrer"
        loadingLabel="Enregistrement..."
      />,
    );

    expect(screen.getByLabelText(/nom de la recette/i)).toHaveValue("Curry de lentilles");
    expect(screen.getByLabelText(/nom de l'ingrédient 1/i)).toHaveValue("lentilles");
    expect(screen.getByLabelText(/quantité de l'ingrédient 1/i)).toHaveValue("200g");
    expect(screen.getByLabelText(/allergènes/i)).toHaveValue("gluten");
    expect(screen.getByLabelText(/nombre de personnes/i)).toHaveValue(4);

    await user.click(screen.getByRole("button", { name: "Enregistrer" }));

    expect(onSubmit).toHaveBeenCalledWith(editInitialValues, false);
  });

  it("shows the existing image with a remove checkbox, and reports removal", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();
    render(
      <AdminRecipeForm
        onSubmit={onSubmit}
        isLoading={false}
        initialValues={editInitialValues}
        existingImageUrl="http://localhost:8000/media/abc.png"
      />,
    );

    expect(screen.getByAltText(/photo actuelle/i)).toBeInTheDocument();

    await user.click(screen.getByLabelText(/supprimer la photo actuelle/i));
    await user.click(screen.getByRole("button", { name: /ajouter la recette/i }));

    expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ image: null }), true);
  });

  it("hides the existing image preview once a replacement is selected", async () => {
    const user = userEvent.setup();
    render(
      <AdminRecipeForm
        onSubmit={vi.fn()}
        isLoading={false}
        initialValues={editInitialValues}
        existingImageUrl="http://localhost:8000/media/abc.png"
      />,
    );
    const file = new File(["fake-bytes"], "new.png", { type: "image/png" });

    await user.upload(screen.getByLabelText(/remplacer la photo/i), file);

    expect(screen.queryByAltText(/photo actuelle/i)).not.toBeInTheDocument();
  });
});
