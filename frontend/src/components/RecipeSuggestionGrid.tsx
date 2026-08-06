import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import RecipeDetailPanel from "./RecipeDetailPanel";
import RecipeSuggestionCard from "./RecipeSuggestionCard";
import type { RecipeSuggestion } from "../types/recipe";
import { DURATION, EASE_OUT, STAGGER } from "../utils/motion";

const EXPANDED_TRACK = "3fr";
const COLLAPSED_TRACK = "1fr";
const NEUTRAL_TRACK = "1fr";

interface RecipeSuggestionGridProps {
  suggestions: RecipeSuggestion[];
  /** Omitted entirely (no watchlist button rendered anywhere) when anonymous. */
  onToggleWatchlist?: (recipeId: number) => void;
  /** The app always provides this (the like count is public). For anonymous
   * visitors the parent routes the click to /login instead of toggling.
   * Optional only so isolated tests can omit it. */
  onToggleLike?: (recipeId: number) => void;
}

// Sizes the 2 tracks on one axis: the active index gets 75% of the axis,
// the other track gets 25% — so the hovered card grows in its own corner
// instead of covering the whole grid, and its siblings shrink but stay
// visible rather than being hidden.
function trackSizes(activeIndex: number | null): string {
  return [0, 1]
    .map((index) => {
      if (activeIndex === null) {
        return NEUTRAL_TRACK;
      }
      return activeIndex === index ? EXPANDED_TRACK : COLLAPSED_TRACK;
    })
    .join(" ");
}

// Touch/coarse-pointer devices have no hover state, so the same onClick that
// opens the detail panel on desktop would fire immediately on tap, skipping
// the expand step entirely. On those devices, a first tap only expands the
// card; a second tap on the already-expanded card opens the detail.
function useCanHover(): boolean {
  const query = "(hover: hover) and (pointer: fine)";
  const [canHover, setCanHover] = useState(
    () => typeof window !== "undefined" && window.matchMedia(query).matches,
  );

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    function handleChange(event: MediaQueryListEvent) {
      setCanHover(event.matches);
    }
    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  return canHover;
}

function RecipeSuggestionGrid({
  suggestions,
  onToggleWatchlist,
  onToggleLike,
}: RecipeSuggestionGridProps) {
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const [openId, setOpenId] = useState<number | null>(null);
  const canHover = useCanHover();
  const prefersReducedMotion = useReducedMotion();
  const lastFocusedElementRef = useRef<HTMLElement | null>(null);

  function openDetail(suggestionId: number) {
    lastFocusedElementRef.current = document.activeElement as HTMLElement | null;
    setOpenId(suggestionId);
  }

  function closeDetail() {
    setOpenId(null);
    setHoveredId(null);
    lastFocusedElementRef.current?.focus();
  }

  function handleCardClick(suggestionId: number) {
    if (canHover || hoveredId === suggestionId) {
      openDetail(suggestionId);
    } else {
      setHoveredId(suggestionId);
    }
  }

  useEffect(() => {
    if (openId === null) {
      return;
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        closeDetail();
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [openId]);

  if (suggestions.length === 0) {
    return null;
  }

  const openSuggestion = suggestions.find((suggestion) => suggestion.id === openId) ?? null;

  const hoveredIndex =
    hoveredId === null ? -1 : suggestions.findIndex((suggestion) => suggestion.id === hoveredId);
  const hoveredRow = hoveredIndex < 0 ? null : Math.floor(hoveredIndex / 2);
  const hoveredCol = hoveredIndex < 0 ? null : hoveredIndex % 2;

  return (
    <>
      <div
        className="grid aspect-square w-full max-w-2xl gap-2"
        style={{
          gridTemplateColumns: trackSizes(hoveredCol),
          gridTemplateRows: trackSizes(hoveredRow),
        }}
        // Handled on the whole grid, not per card: moving the mouse directly
        // from one card to another must not pass through a "nothing hovered"
        // state in between, or the layout animation flashes back to neutral
        // before re-expanding the new card. Same idea for onBlur/keyboard
        // focus leaving the whole grid.
        onMouseLeave={() => setHoveredId(null)}
        onBlur={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
            setHoveredId(null);
          }
        }}
      >
        {suggestions.map((suggestion, index) => (
          <motion.div
            key={suggestion.id}
            layout
            style={{ transformPerspective: 1200 }}
            // Cards fade in with a 60ms stagger on mount (docs/FRONTEND.md §6.2).
            // Opacity only, not y: a manual translate would fight the `layout`
            // transform on this same element used for the corner-grow resize.
            initial={{ opacity: 0 }}
            // Driven by our own hoveredId state rather than Framer's whileHover:
            // whileHover tracks native hover on this exact element, but rotating
            // it changes its own on-screen hit-test shape near 90°/270°, which
            // can drop and re-trigger hover mid-spin. Our hoveredId is derived
            // from the (non-rotating) grid container's mouseLeave, so it stays
            // stable regardless of what the rotation does to this element.
            animate={
              prefersReducedMotion
                ? { opacity: 1 }
                : { opacity: 1, rotateY: hoveredId === suggestion.id ? 360 : 0 }
            }
            transition={{
              opacity: { duration: DURATION.enter, ease: EASE_OUT, delay: index * STAGGER },
              layout: { duration: 0.4, ease: "easeInOut" },
              rotateY: { duration: 0.6, ease: "easeInOut" },
            }}
            className="min-h-0 min-w-0"
          >
            <RecipeSuggestionCard
              suggestion={suggestion}
              onMouseEnter={() => setHoveredId(suggestion.id)}
              onFocus={() => setHoveredId(suggestion.id)}
              onClick={() => handleCardClick(suggestion.id)}
              expanded={hoveredId === suggestion.id}
              hint={
                !canHover && hoveredId === suggestion.id
                  ? "Toucher à nouveau pour voir la recette"
                  : undefined
              }
              onToggleWatchlist={
                onToggleWatchlist ? () => onToggleWatchlist(suggestion.id) : undefined
              }
            />
          </motion.div>
        ))}
      </div>

      <AnimatePresence>
        {openSuggestion && (
          <RecipeDetailPanel
            key="recipe-detail-panel"
            suggestion={openSuggestion}
            onClose={closeDetail}
            onToggleWatchlist={
              onToggleWatchlist ? () => onToggleWatchlist(openSuggestion.id) : undefined
            }
            onToggleLike={onToggleLike ? () => onToggleLike(openSuggestion.id) : undefined}
          />
        )}
      </AnimatePresence>
    </>
  );
}

export default RecipeSuggestionGrid;
