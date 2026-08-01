import { SearchX, TriangleAlert } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";
import { fetchSuggestions } from "../api/suggestions";
import { AnimatedTitle } from "../components/AnimatedTitle";
import { AppShell } from "../components/AppShell";
import { Header } from "../components/Header";
import RecipeForm from "../components/RecipeForm";
import RecipeSuggestionGrid from "../components/RecipeSuggestionGrid";
import { Reveal } from "../components/Reveal";
import { SourceRecipeSummary } from "../components/SourceRecipeSummary";
import { Eyebrow } from "../components/ui/Eyebrow";
import { EmptyState } from "../components/ui/EmptyState";
import { Skeleton } from "../components/ui/Skeleton";
import type { RecipeSuggestion } from "../types/recipe";

// The highlighted noun cycles through these in the hero headline (§6.1).
const HERO_WORDS = [
  "bœuf bourguignon",
  "poulet rôti",
  "carbonara",
  "chili con carne",
  "blanquette de veau",
];

interface SubmittedQuery {
  title: string;
  ingredients: string[];
}

function HomePage() {
  const [suggestions, setSuggestions] = useState<RecipeSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submittedQuery, setSubmittedQuery] = useState<SubmittedQuery | null>(null);

  async function handleSubmit(title: string, ingredients: string[]) {
    setIsLoading(true);
    setError(null);
    setSubmittedQuery({ title, ingredients });
    try {
      const response = await fetchSuggestions(title, ingredients);
      setSuggestions(response.suggestions);
    } catch {
      setError("Impossible de récupérer des suggestions pour le moment.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AppShell>
      <Header
        actions={
          <Link
            to="/admin/login"
            className="rounded-md px-3 py-2 text-sm text-sauge transition-colors hover:bg-feuille-haut hover:text-craie focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse"
          >
            Espace admin
          </Link>
        }
      />

      <main>
        <section className="relative isolate pt-8 pb-4">
          {/* Ambient: one soft pousse radial behind the headline, static (§6.1). */}
          <div
            aria-hidden="true"
            className="pointer-events-none absolute top-[-6rem] left-1/2 -z-10 h-[520px] w-[720px] max-w-full -translate-x-1/2"
            style={{
              background:
                "radial-gradient(circle at center, color-mix(in oklab, var(--color-pousse) 7%, transparent) 0%, transparent 68%)",
            }}
          />

          <Reveal>
            <Eyebrow>Recherche de substitution</Eyebrow>
          </Reveal>
          <AnimatedTitle
            prefix="Votre"
            words={HERO_WORDS}
            suffix=", en version végétarienne."
            className="mt-4 max-w-3xl"
          />
          <Reveal delay={0.12}>
            <p className="mt-5 max-w-[68ch] text-lg text-sauge">
              Décrivez un plat que vous aimez : on vous propose quatre recettes végétariennes
              proches par le goût et la composition.
            </p>
          </Reveal>
          <Reveal delay={0.22} className="mt-8">
            <RecipeForm onSubmit={handleSubmit} isLoading={isLoading} />
          </Reveal>
        </section>

        <section aria-live="polite" className="pb-24">
          {submittedQuery && (
            <div className="mt-12 border-t border-lisiere pt-10">
              <SourceRecipeSummary
                title={submittedQuery.title}
                ingredients={submittedQuery.ingredients}
              />

              {error ? (
                <EmptyState
                  className="mt-8"
                  icon={TriangleAlert}
                  title="La recherche n'a pas abouti"
                  description="Vérifiez votre connexion, puis relancez la recherche."
                />
              ) : isLoading ? (
                <div className="mt-8 flex justify-center">
                  <div className="grid aspect-square w-full max-w-2xl grid-cols-2 grid-rows-2 gap-2">
                    {[0, 1, 2, 3].map((slot) => (
                      <Skeleton key={slot} className="h-full w-full rounded-lg" />
                    ))}
                  </div>
                </div>
              ) : suggestions.length === 0 ? (
                <EmptyState
                  className="mt-8"
                  icon={SearchX}
                  title="Aucune recette proche pour l'instant"
                  description="Essayez avec moins d'ingrédients ou un titre plus courant."
                />
              ) : (
                <>
                  <h2 className="mt-8 font-display text-2xl text-craie">
                    {suggestions.length} alternatives végétariennes
                  </h2>
                  <div className="mt-6 flex justify-center">
                    <RecipeSuggestionGrid suggestions={suggestions} />
                  </div>
                </>
              )}
            </div>
          )}
        </section>
      </main>
    </AppShell>
  );
}

export default HomePage;
