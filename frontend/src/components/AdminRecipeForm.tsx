import { X } from "lucide-react";
import { useState, type FormEvent } from "react";
import ProteinSourceCombobox from "./ProteinSourceCombobox";
import { Button } from "./ui/Button";
import type { DishStructureOptions, RecipeFormValues } from "../types/recipe";

interface AdminRecipeFormProps {
  onSubmit: (values: RecipeFormValues, removeExistingImage: boolean) => void;
  isLoading: boolean;
  /** Prefills the form for editing an existing recipe; omit for "add new". */
  initialValues?: RecipeFormValues;
  /** Full URL (already prefixed with the API base) of the recipe's current
   * image, if any — shown with a checkbox to remove it. Edit mode only. */
  existingImageUrl?: string | null;
  /** Known protein_source vocabulary (see matching/substitution.py), fetched
   * by the parent page — the combobox only ever commits one of these. */
  proteinSourceOptions?: string[];
  /** Dish type and cuisine vocabularies (see matching/dish_structure.py),
   * fetched by the parent page. */
  dishStructureOptions?: DishStructureOptions;
  submitLabel?: string;
  loadingLabel?: string;
}

interface IngredientRow {
  name: string;
  quantity: string;
}

const EMPTY_INGREDIENT_ROW: IngredientRow = { name: "", quantity: "" };

const NO_DISH_STRUCTURE_OPTIONS: DishStructureOptions = { dish_types: [], cuisines: [] };

/** The vocabulary plus anything already selected that it doesn't list, so a
 * recipe's tags stay visible (and are saved back) even if the options failed
 * to load. */
function withSelected(options: string[], selected: string[]): string[] {
  return [...options, ...selected.filter((value) => !options.includes(value))];
}

export const inputClassName =
  "rounded-md border border-lisiere bg-feuille-haut px-3 py-2 text-craie focus:border-pousse focus:ring-2 focus:ring-pousse/25 focus:outline-none";
export const labelClassName = "flex flex-col gap-1 text-left text-sm font-medium text-craie";

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
  proteinSourceOptions = [],
  dishStructureOptions = NO_DISH_STRUCTURE_OPTIONS,
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
  const [proteinSource, setProteinSource] = useState<string | null>(
    initialValues?.proteinSource ?? null,
  );
  const [proteinGramsText, setProteinGramsText] = useState(
    initialValues?.proteinGrams?.toString() ?? "",
  );
  const [caloriesText, setCaloriesText] = useState(
    initialValues?.caloriesPerPortion?.toString() ?? "",
  );
  const [priceTier, setPriceTier] = useState<number | null>(initialValues?.priceTier ?? null);
  const [dishTypes, setDishTypes] = useState<string[]>(initialValues?.dishTypes ?? []);
  const [cuisine, setCuisine] = useState<string | null>(initialValues?.cuisine ?? null);
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

  function toggleDishType(dishType: string, checked: boolean) {
    setDishTypes((current) =>
      checked ? [...current, dishType] : current.filter((value) => value !== dishType),
    );
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
    const caloriesPerPortion = caloriesText.trim() ? Number(caloriesText.trim()) : null;
    onSubmit(
      {
        title,
        ingredients,
        allergens,
        prepTimeMinutes,
        servings,
        proteinSource,
        proteinGrams,
        caloriesPerPortion,
        priceTier,
        dishTypes,
        cuisine,
        instructions,
        image,
      },
      removeExistingImage,
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-[640px] flex-col gap-4">
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
        <span className="text-sm font-medium text-craie">
          Ingrédients
          {quantityRequired && (
            <span className="text-sauge">
              {" "}
              (quantité obligatoire, le nombre de personnes est renseigné)
            </span>
          )}
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
                className="rounded-sm px-1 text-sauge transition-colors hover:text-brique focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
              >
                <X className="size-4" aria-hidden="true" />
              </button>
            )}
          </div>
        ))}
        <button
          type="button"
          onClick={addIngredientRow}
          className="self-start rounded-sm text-sm font-medium text-pousse transition-colors hover:text-pousse-clair focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
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
      <ProteinSourceCombobox
        value={proteinSource}
        onChange={setProteinSource}
        options={proteinSourceOptions}
      />
      <label className={labelClassName}>
        Protéines en grammes par portion (optionnel)
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
        Calories par portion (optionnel)
        <input
          type="number"
          min={0}
          step="any"
          value={caloriesText}
          onChange={(event) => setCaloriesText(event.target.value)}
          placeholder="420"
          className={inputClassName}
        />
      </label>
      <label className={labelClassName}>
        Niveau de prix (optionnel)
        <select
          value={priceTier === null ? "" : String(priceTier)}
          onChange={(event) =>
            setPriceTier(event.target.value === "" ? null : Number(event.target.value))
          }
          className={inputClassName}
        >
          <option value="">Non précisé</option>
          <option value="1">€ — économique</option>
          <option value="2">€€ — intermédiaire</option>
          <option value="3">€€€ — coûteux</option>
        </select>
      </label>
      <fieldset className="flex flex-col gap-2">
        <legend className="mb-2 text-left text-sm font-medium text-craie">
          Types de plat (optionnel)
        </legend>
        <div className="flex flex-wrap gap-2">
          {withSelected(dishStructureOptions.dish_types, dishTypes).map((dishType) => (
            <label
              key={dishType}
              className="inline-flex items-center gap-1.5 rounded-md border border-lisiere px-2 py-1 text-sm text-craie has-[:checked]:border-pousse"
            >
              <input
                type="checkbox"
                checked={dishTypes.includes(dishType)}
                onChange={(event) => toggleDishType(dishType, event.target.checked)}
                className="accent-pousse"
              />
              {dishType}
            </label>
          ))}
        </div>
      </fieldset>
      <label className={labelClassName}>
        Cuisine (optionnel)
        <select
          value={cuisine ?? ""}
          onChange={(event) => setCuisine(event.target.value === "" ? null : event.target.value)}
          className={inputClassName}
        >
          <option value="">Non précisée</option>
          {withSelected(dishStructureOptions.cuisines, cuisine === null ? [] : [cuisine]).map(
            (option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ),
          )}
        </select>
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
          <span className="text-sm font-medium text-craie">Photo actuelle</span>
          <img
            src={existingImageUrl}
            alt="Photo actuelle de la recette"
            className="max-h-32 rounded-md border border-lisiere"
          />
          <label className="flex items-center gap-2 text-sm text-sauge">
            <input
              type="checkbox"
              checked={removeExistingImage}
              onChange={(event) => setRemoveExistingImage(event.target.checked)}
              className="accent-pousse"
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

      <Button type="submit" size="lg" loading={isLoading} className="self-start">
        {isLoading ? loadingLabel : submitLabel}
      </Button>
    </form>
  );
}

export default AdminRecipeForm;
