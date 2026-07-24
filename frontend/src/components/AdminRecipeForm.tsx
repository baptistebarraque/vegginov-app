import { useState, type FormEvent } from "react";
import type { RecipeFormValues } from "../types/recipe";

interface AdminRecipeFormProps {
  onSubmit: (values: RecipeFormValues, removeExistingImage: boolean) => void;
  isLoading: boolean;
  /** Prefills the form for editing an existing recipe; omit for "add new". */
  initialValues?: RecipeFormValues;
  /** Full URL (already prefixed with the API base) of the recipe's current
   * image, if any — shown with a checkbox to remove it. Edit mode only. */
  existingImageUrl?: string | null;
  submitLabel?: string;
  loadingLabel?: string;
}

interface IngredientRow {
  name: string;
  quantity: string;
}

const EMPTY_INGREDIENT_ROW: IngredientRow = { name: "", quantity: "" };

const inputClassName =
  "rounded border border-neutral-300 px-3 py-2 text-neutral-900 focus:border-green-600 focus:outline-none dark:border-neutral-700 dark:bg-neutral-800 dark:text-white";
const labelClassName = "flex flex-col gap-1 text-left text-sm text-neutral-700 dark:text-neutral-300";

function toIngredientRows(initialValues: RecipeFormValues | undefined): IngredientRow[] {
  if (!initialValues || initialValues.ingredients.length === 0) {
    return [EMPTY_INGREDIENT_ROW];
  }
  return initialValues.ingredients.map((ingredient) => ({
    name: ingredient.name,
    quantity: ingredient.quantity ?? "",
  }));
}

function AdminRecipeForm({
  onSubmit,
  isLoading,
  initialValues,
  existingImageUrl = null,
  submitLabel = "Ajouter la recette",
  loadingLabel = "Ajout...",
}: AdminRecipeFormProps) {
  const [title, setTitle] = useState(initialValues?.title ?? "");
  const [ingredientRows, setIngredientRows] = useState<IngredientRow[]>(
    toIngredientRows(initialValues),
  );
  const [allergensText, setAllergensText] = useState(initialValues?.allergens.join(", ") ?? "");
  const [prepTimeText, setPrepTimeText] = useState(
    initialValues?.prepTimeMinutes?.toString() ?? "",
  );
  const [servingsText, setServingsText] = useState(initialValues?.servings?.toString() ?? "");
  const [proteinSource, setProteinSource] = useState(initialValues?.proteinSource ?? "");
  const [proteinGramsText, setProteinGramsText] = useState(
    initialValues?.proteinGrams?.toString() ?? "",
  );
  const [instructionsText, setInstructionsText] = useState(
    initialValues?.instructions.join("\n") ?? "",
  );
  const [image, setImage] = useState<File | null>(null);
  const [removeExistingImage, setRemoveExistingImage] = useState(false);

  const quantityRequired = servingsText.trim() !== "";

  function updateIngredientRow(index: number, field: keyof IngredientRow, value: string) {
    setIngredientRows((rows) =>
      rows.map((row, rowIndex) => (rowIndex === index ? { ...row, [field]: value } : row)),
    );
  }

  function addIngredientRow() {
    setIngredientRows((rows) => [...rows, EMPTY_INGREDIENT_ROW]);
  }

  function removeIngredientRow(index: number) {
    setIngredientRows((rows) => rows.filter((_, rowIndex) => rowIndex !== index));
  }

  function handleImageChange(file: File | null) {
    setImage(file);
    if (file !== null) {
      setRemoveExistingImage(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const ingredients = ingredientRows
      .map((row) => ({ name: row.name.trim(), quantity: row.quantity.trim() || null }))
      .filter((ingredient) => ingredient.name !== "");
    const allergens = allergensText
      .split(",")
      .map((allergen) => allergen.trim())
      .filter(Boolean);
    const instructions = instructionsText
      .split("\n")
      .map((step) => step.trim())
      .filter(Boolean);
    const prepTimeMinutes = prepTimeText.trim() ? Number(prepTimeText.trim()) : null;
    const servings = servingsText.trim() ? Number(servingsText.trim()) : null;
    const proteinGrams = proteinGramsText.trim() ? Number(proteinGramsText.trim()) : null;
    onSubmit(
      {
        title,
        ingredients,
        allergens,
        prepTimeMinutes,
        servings,
        proteinSource: proteinSource.trim() || null,
        proteinGrams,
        instructions,
        image,
      },
      removeExistingImage,
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-md flex-col gap-3">
      <label className={labelClassName}>
        Nom de la recette
        <input
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          required
          placeholder="Curry de lentilles corail"
          className={inputClassName}
        />
      </label>

      <div className="flex flex-col gap-2">
        <span className="text-sm text-neutral-700 dark:text-neutral-300">
          Ingrédients{quantityRequired && " (quantité obligatoire, le nombre de personnes est renseigné)"}
        </span>
        {ingredientRows.map((row, index) => (
          <div key={index} className="flex gap-2">
            <input
              type="text"
              value={row.name}
              onChange={(event) => updateIngredientRow(index, "name", event.target.value)}
              placeholder="Riz"
              aria-label={`Nom de l'ingrédient ${index + 1}`}
              className={`${inputClassName} flex-1`}
            />
            <input
              type="text"
              value={row.quantity}
              onChange={(event) => updateIngredientRow(index, "quantity", event.target.value)}
              placeholder="200g"
              aria-label={`Quantité de l'ingrédient ${index + 1}`}
              className={`${inputClassName} w-24`}
            />
            {ingredientRows.length > 1 && (
              <button
                type="button"
                onClick={() => removeIngredientRow(index)}
                aria-label={`Supprimer l'ingrédient ${index + 1}`}
                className="text-neutral-500 hover:text-red-600 dark:text-neutral-400 dark:hover:text-red-400"
              >
                ✕
              </button>
            )}
          </div>
        ))}
        <button
          type="button"
          onClick={addIngredientRow}
          className="self-start text-sm text-green-700 underline hover:text-green-800 dark:text-green-400 dark:hover:text-green-300"
        >
          + Ajouter un ingrédient
        </button>
      </div>

      <label className={labelClassName}>
        Allergènes (optionnel, séparés par des virgules)
        <input
          type="text"
          value={allergensText}
          onChange={(event) => setAllergensText(event.target.value)}
          placeholder="gluten, lactose"
          className={inputClassName}
        />
      </label>
      <label className={labelClassName}>
        Temps de préparation en minutes (optionnel)
        <input
          type="number"
          min={0}
          value={prepTimeText}
          onChange={(event) => setPrepTimeText(event.target.value)}
          placeholder="25"
          className={inputClassName}
        />
      </label>
      <label className={labelClassName}>
        Nombre de personnes (optionnel)
        <input
          type="number"
          min={1}
          value={servingsText}
          onChange={(event) => setServingsText(event.target.value)}
          placeholder="4"
          className={inputClassName}
        />
      </label>
      <label className={labelClassName}>
        Source de protéines (optionnel)
        <input
          type="text"
          value={proteinSource}
          onChange={(event) => setProteinSource(event.target.value)}
          placeholder="lentilles corail"
          className={inputClassName}
        />
      </label>
      <label className={labelClassName}>
        Protéines en grammes (optionnel)
        <input
          type="number"
          min={0}
          step="any"
          value={proteinGramsText}
          onChange={(event) => setProteinGramsText(event.target.value)}
          placeholder="18.5"
          className={inputClassName}
        />
      </label>
      <label className={labelClassName}>
        Étapes de préparation (optionnel, une étape par ligne)
        <textarea
          value={instructionsText}
          onChange={(event) => setInstructionsText(event.target.value)}
          rows={5}
          placeholder={"Faire revenir les oignons\nAjouter les lentilles et le curry\n..."}
          className={inputClassName}
        />
      </label>

      {existingImageUrl !== null && !removeExistingImage && image === null && (
        <div className="flex flex-col gap-1">
          <span className="text-sm text-neutral-700 dark:text-neutral-300">Photo actuelle</span>
          <img
            src={existingImageUrl}
            alt="Photo actuelle de la recette"
            className="max-h-32 rounded"
          />
          <label className="flex items-center gap-2 text-sm text-neutral-700 dark:text-neutral-300">
            <input
              type="checkbox"
              checked={removeExistingImage}
              onChange={(event) => setRemoveExistingImage(event.target.checked)}
            />
            Supprimer la photo actuelle
          </label>
        </div>
      )}
      <label className={labelClassName}>
        {existingImageUrl !== null ? "Remplacer la photo (PNG ou JPEG)" : "Photo de la recette (optionnel, PNG ou JPEG)"}
        <input
          type="file"
          accept="image/png,image/jpeg"
          onChange={(event) => handleImageChange(event.target.files?.[0] ?? null)}
          className={inputClassName}
        />
      </label>

      <button
        type="submit"
        disabled={isLoading}
        className="rounded bg-green-700 px-4 py-2 font-medium text-white transition hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isLoading ? loadingLabel : submitLabel}
      </button>
    </form>
  );
}

export default AdminRecipeForm;
