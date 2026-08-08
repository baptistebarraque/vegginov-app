import { SearchX, TriangleAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import { getCurrentUser } from "../api/auth";
import { likeRecipe, unlikeRecipe } from "../api/likes";
import { fetchSuggestions } from "../api/suggestions";
import { addToWatchlist, removeFromWatchlist } from "../api/watchlist";
import { AnimatedTitle } from "../components/AnimatedTitle";
import { AppShell } from "../components/AppShell";
import { Header } from "../components/Header";
import RecipeForm from "../components/RecipeForm";
import RecipeSuggestionGrid from "../components/RecipeSuggestionGrid";
import { Reveal } from "../components/Reveal";
import { SourceRecipeSummary } from "../components/SourceRecipeSummary";
import { BeanToggle } from "../components/ui/BeanToggle";
import { Button } from "../components/ui/Button";
import { Eyebrow } from "../components/ui/Eyebrow";
import { EmptyState } from "../components/ui/EmptyState";
import { Skeleton } from "../components/ui/Skeleton";
import type { User } from "../types/auth";
import type { RecipeSuggestion } from "../types/recipe";

const headerLinkClassName =
  "rounded-md px-3 py-2 text-sm text-sauge transition-colors hover:bg-feuille-haut hover:text-craie focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse";

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

// The grid always shows 4 recipes at a time. The API actually ranks and
// returns up to 12 (recipe_service.SUGGESTION_COUNT) in one response — the
// "Charger plus de recettes" button pages through the rest of that same
// batch client-side rather than issuing a new search, then wraps back to
// the top once every ranked recipe has been shown.
const PAGE_SIZE = 4;

function HomePage() {
  const [suggestions, setSuggestions] = useState<RecipeSuggestion[]>([]);
  const [page, setPage] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submittedQuery, setSubmittedQuery] = useState<SubmittedQuery | null>(null);
  const [user, setUser] = useState<User | null>(null);
  // Applying the profile's preferences is the default when signed in; the
  // user can opt out per search. Sent to the API as its inverse (ignore flag).
  const [applyPreferences, setApplyPreferences] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Anonymous browsing (suggestions) is fully supported — this only
    // decides what the header shows, it never gates the page.
    getCurrentUser()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  async function handleSubmit(title: string, ingredients: string[]) {
    setIsLoading(true);
    setError(null);
    setSubmittedQuery({ title, ingredients });
    setPage(0);
    try {
      const response = await fetchSuggestions(title, ingredients, !applyPreferences);
      setSuggestions(response.suggestions);
    } catch {
      setError("Impossible de récupérer des suggestions pour le moment.");
    } finally {
      setIsLoading(false);
    }
  }

  function setWatchlisted(recipeId: number, value: boolean) {
    setSuggestions((current) =>
      current.map((suggestion) =>
        suggestion.id === recipeId ? { ...suggestion, is_watchlisted: value } : suggestion,
      ),
    );
  }

  async function handleToggleWatchlist(recipeId: number) {
    const current = suggestions.find((suggestion) => suggestion.id === recipeId);
    if (!current) {
      return;
    }
    const wasWatchlisted = current.is_watchlisted;
    // Optimistic: flip immediately, revert if the request fails.
    setWatchlisted(recipeId, !wasWatchlisted);
    try {
      if (wasWatchlisted) {
        await removeFromWatchlist(recipeId);
      } else {
        await addToWatchlist(recipeId);
      }
    } catch {
      setWatchlisted(recipeId, wasWatchlisted);
    }
  }

  function setLikeState(recipeId: number, isLiked: boolean, likeCount: number) {
    setSuggestions((current) =>
      current.map((suggestion) =>
        suggestion.id === recipeId
          ? { ...suggestion, is_liked: isLiked, like_count: likeCount }
          : suggestion,
      ),
    );
  }

  async function handleToggleLike(recipeId: number) {
    // The like count is public, so the heart renders even when logged out —
    // but liking needs an account. Send anonymous visitors to sign in.
    if (!user) {
      navigate("/login");
      return;
    }
    const current = suggestions.find((suggestion) => suggestion.id === recipeId);
    if (!current) {
      return;
    }
    const wasLiked = current.is_liked;
    const previousCount = current.like_count;
    // Optimistic: flip and adjust the count immediately, revert if it fails.
    setLikeState(recipeId, !wasLiked, previousCount + (wasLiked ? -1 : 1));
    try {
      const status = wasLiked ? await unlikeRecipe(recipeId) : await likeRecipe(recipeId);
      // Reconcile with the server's authoritative count (other users may have
      // liked it since this page loaded).
      setLikeState(recipeId, status.isLiked, status.likeCount);
    } catch {
      setLikeState(recipeId, wasLiked, previousCount);
    }
  }

  const pageCount = Math.ceil(suggestions.length / PAGE_SIZE);
  const visibleSuggestions = suggestions.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE);

  function handleLoadMore() {
    setPage((current) => (current + 1) % pageCount);
  }

  return (
    <AppShell>
      <Header
        actions={
          <>
            {user ? (
              <>
                <Link to="/watchlist" className={headerLinkClassName}>
                  Ma liste
                </Link>
                <Link to="/likes" className={headerLinkClassName}>
                  Coups de cœur
                </Link>
                <Link to="/account" className={headerLinkClassName}>
                  {user.email}
                </Link>
              </>
            ) : (
              <Link to="/login" className={headerLinkClassName}>
                Se connecter
              </Link>
            )}
            {user?.isAdmin && (
              // Already authenticated (as an admin) to get this link at all,
              // so it goes straight into the admin panel, not back through
              // a login form.
              <Link to="/admin" className={headerLinkClassName}>
                Espace admin
              </Link>
            )}
          </>
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
            {user && (
              <BeanToggle
                className="mt-3"
                checked={applyPreferences}
                onChange={setApplyPreferences}
                label="Appliquer les préférences du profil (allergènes, budget, calories)"
              />
            )}
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
                    {visibleSuggestions.length} alternatives végétariennes
                  </h2>
                  <div className="mt-6 flex justify-center">
                    <RecipeSuggestionGrid
                      key={page}
                      suggestions={visibleSuggestions}
                      onToggleWatchlist={user ? handleToggleWatchlist : undefined}
                      onToggleLike={handleToggleLike}
                    />
                  </div>
                  {pageCount > 1 && (
                    <div className="mt-8 flex justify-center">
                      <Button variant="secondary" onClick={handleLoadMore}>
                        Charger plus de recettes
                      </Button>
                    </div>
                  )}
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
