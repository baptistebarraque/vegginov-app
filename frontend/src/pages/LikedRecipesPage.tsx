import { Heart } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { logout } from "../api/auth";
import { getLikes, unlikeRecipe } from "../api/likes";
import { AppShell } from "../components/AppShell";
import { Header } from "../components/Header";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { EmptyState } from "../components/ui/EmptyState";
import { Skeleton } from "../components/ui/Skeleton";
import { useSession } from "../hooks/useSession";
import type { LikedRecipe } from "../types/like";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

interface LikedRecipeRowProps {
  recipe: LikedRecipe;
  onRemove: () => Promise<void>;
}

function LikedRecipeRow({ recipe, onRemove }: LikedRecipeRowProps) {
  const [isRemoving, setIsRemoving] = useState(false);

  async function handleRemove() {
    setIsRemoving(true);
    try {
      await onRemove();
    } catch {
      setIsRemoving(false);
    }
  }

  return (
    <div className="flex items-center gap-4 rounded-lg border border-lisiere bg-feuille p-4">
      {recipe.imageUrl && (
        <img
          src={`${API_BASE_URL}${recipe.imageUrl}`}
          alt={recipe.title}
          className="h-20 w-20 shrink-0 rounded-md object-contain"
        />
      )}
      <div className="flex flex-1 flex-col gap-1">
        <h3 className="font-display text-lg text-craie">{recipe.title}</h3>
        <p className="inline-flex items-center gap-1.5 text-sm text-sauge">
          <Heart className="size-4 text-pousse" fill="currentColor" aria-hidden="true" />
          <span className="font-mono tabular-nums">{recipe.likeCount}</span>
          {recipe.likeCount > 1 ? "personnes aiment" : "personne aime"} cette recette
        </p>
      </div>
      <Button size="sm" variant="ghost" loading={isRemoving} onClick={handleRemove}>
        Ne plus aimer
      </Button>
    </div>
  );
}

function LikedRecipesPage() {
  const { user, isChecking } = useSession();
  const [recipes, setRecipes] = useState<LikedRecipe[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (user === null) {
      return;
    }
    getLikes()
      .then(setRecipes)
      .catch(() => setLoadError("Impossible de charger vos coups de cœur."));
  }, [user]);

  async function handleRemove(recipeId: number) {
    await unlikeRecipe(recipeId);
    setRecipes((current) => (current ?? []).filter((recipe) => recipe.recipeId !== recipeId));
  }

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  if (isChecking || user === null) {
    return null;
  }

  return (
    <AppShell>
      <Header
        section="Mes coups de cœur"
        actions={
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            Se déconnecter
          </Button>
        }
      />

      <main className="pb-24">
        <h1 className="font-display text-3xl text-craie">Mes coups de cœur</h1>
        <p className="mt-1 text-sm text-sauge">Les recettes que vous avez aimées.</p>

        <div className="mt-8 flex max-w-[560px] flex-col gap-4">
          {loadError ? (
            <Alert variant="error">{loadError}</Alert>
          ) : recipes === null ? (
            [0, 1, 2].map((slot) => <Skeleton key={slot} className="h-28 w-full" />)
          ) : recipes.length === 0 ? (
            <EmptyState
              icon={Heart}
              title="Aucun coup de cœur pour l'instant"
              description="Aimez une recette depuis la page d'accueil pour la retrouver ici."
            />
          ) : (
            recipes.map((recipe) => (
              <LikedRecipeRow
                key={recipe.recipeId}
                recipe={recipe}
                onRemove={() => handleRemove(recipe.recipeId)}
              />
            ))
          )}
        </div>
      </main>
    </AppShell>
  );
}

export default LikedRecipesPage;
