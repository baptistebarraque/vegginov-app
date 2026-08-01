import { cn } from "../utils/cn";
import { Eyebrow } from "./ui/Eyebrow";

interface SourceRecipeSummaryProps {
  title: string;
  ingredients: string[];
  className?: string;
}

// Echoes the dish the user searched with (docs/FRONTEND.md §6.2). The betterave
// left rule + eyebrow mark "the dish you came in with"; it is the only beetroot
// element on the results screen.
function SourceRecipeSummary({ title, ingredients, className }: SourceRecipeSummaryProps) {
  return (
    <div className={cn("border-l-2 border-betterave pl-4", className)}>
      <Eyebrow className="text-betterave">Votre recette</Eyebrow>
      <p className="mt-1 font-display text-xl text-craie">{title}</p>
      {ingredients.length > 0 && (
        <p className="mt-0.5 text-sm text-sauge">{ingredients.join(", ")}</p>
      )}
    </div>
  );
}

export { SourceRecipeSummary };
