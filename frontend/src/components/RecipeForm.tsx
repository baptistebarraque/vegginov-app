import { useState, type FormEvent } from "react";
import { Button } from "./ui/Button";
import { Input } from "./ui/Input";
import { Label } from "./ui/Label";
import { Textarea } from "./ui/Textarea";

interface RecipeFormProps {
  onSubmit: (title: string, ingredients: string[]) => void;
  isLoading: boolean;
}

function RecipeForm({ onSubmit, isLoading }: RecipeFormProps) {
  const [title, setTitle] = useState("");
  const [ingredientsText, setIngredientsText] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const ingredients = ingredientsText
      .split(",")
      .map((ingredient) => ingredient.trim())
      .filter(Boolean);
    onSubmit(title, ingredients);
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-xl flex-col gap-4 text-left">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="recipe-title">Nom de la recette</Label>
        <Input
          id="recipe-title"
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          required
          placeholder="Poulet au curry"
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="recipe-ingredients">Ingrédients (séparés par des virgules)</Label>
        <Textarea
          id="recipe-ingredients"
          value={ingredientsText}
          onChange={(event) => setIngredientsText(event.target.value)}
          placeholder="poulet, curry, lait de coco"
          rows={3}
        />
      </div>
      <Button type="submit" size="lg" loading={isLoading} className="self-start">
        {isLoading ? "Recherche…" : "Trouver des recettes"}
      </Button>
    </form>
  );
}

export default RecipeForm;
