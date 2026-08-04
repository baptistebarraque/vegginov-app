import { useState, type FormEvent } from "react";
import { inputClassName, labelClassName } from "./AdminRecipeForm";
import { Button } from "./ui/Button";
import type { Preferences } from "../types/preference";

interface PreferenceFormProps {
  initialValues?: Preferences;
  onSubmit: (values: Preferences) => void;
  isLoading: boolean;
  submitLabel?: string;
  loadingLabel?: string;
}

const EMPTY_PREFERENCES: Preferences = {
  calorieOrientation: null,
  diet: null,
  allergens: [],
  priceRange: null,
};

// Shared by OnboardingPage (right after signup) and ProfilePreferencesPage
// (editable any time) — same fields, same validation, one implementation.
function PreferenceForm({
  initialValues = EMPTY_PREFERENCES,
  onSubmit,
  isLoading,
  submitLabel = "Enregistrer",
  loadingLabel = "Enregistrement…",
}: PreferenceFormProps) {
  const [calorieOrientation, setCalorieOrientation] = useState(initialValues.calorieOrientation);
  const [diet, setDiet] = useState(initialValues.diet);
  const [allergensText, setAllergensText] = useState(initialValues.allergens.join(", "));
  const [priceRange, setPriceRange] = useState(initialValues.priceRange);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const allergens = allergensText
      .split(",")
      .map((allergen) => allergen.trim())
      .filter((allergen) => allergen.length > 0);
    onSubmit({ calorieOrientation, diet, allergens, priceRange });
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <label className={labelClassName}>
        Orientation calorique (optionnel)
        <select
          value={calorieOrientation ?? ""}
          onChange={(event) =>
            setCalorieOrientation(
              event.target.value === "" ? null : (event.target.value as Preferences["calorieOrientation"]),
            )
          }
          className={inputClassName}
        >
          <option value="">Non précisé</option>
          <option value="low">Basse calorie</option>
          <option value="balanced">Équilibré</option>
          <option value="high">Riche (prise de masse)</option>
        </select>
      </label>

      <label className={labelClassName}>
        Régime alimentaire (optionnel)
        <select
          value={diet ?? ""}
          onChange={(event) =>
            setDiet(event.target.value === "" ? null : (event.target.value as Preferences["diet"]))
          }
          className={inputClassName}
        >
          <option value="">Non précisé</option>
          <option value="omnivore">Omnivore</option>
          <option value="vegetarian">Végétarien</option>
          <option value="pescatarian">Pescétarien</option>
          <option value="vegan">Végane</option>
        </select>
      </label>

      <label className={labelClassName}>
        Allergènes à exclure (optionnel, séparés par une virgule)
        <input
          type="text"
          value={allergensText}
          onChange={(event) => setAllergensText(event.target.value)}
          placeholder="gluten, lactose, fruits à coque"
          className={inputClassName}
        />
      </label>

      <label className={labelClassName}>
        Budget (optionnel)
        <select
          value={priceRange === null ? "" : String(priceRange)}
          onChange={(event) =>
            setPriceRange(event.target.value === "" ? null : Number(event.target.value))
          }
          className={inputClassName}
        >
          <option value="">Non précisé</option>
          <option value="1">€ — économique</option>
          <option value="2">€€ — intermédiaire</option>
          <option value="3">€€€ — coûteux</option>
        </select>
      </label>

      <Button type="submit" loading={isLoading} className="mt-1">
        {isLoading ? loadingLabel : submitLabel}
      </Button>
    </form>
  );
}

export default PreferenceForm;
