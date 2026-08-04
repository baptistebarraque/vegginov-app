import { Bookmark } from "lucide-react";
import { cn } from "../utils/cn";

interface WatchlistButtonProps {
  isWatchlisted: boolean;
  onToggle: () => void;
  loading?: boolean;
  className?: string;
}

// Toggles a recipe's presence in the current user's watchlist. Rendered as a
// sibling overlay on recipe cards (not nested inside the card's own button —
// two interactive elements can't nest) and inline in the detail panel.
function WatchlistButton({ isWatchlisted, onToggle, loading = false, className }: WatchlistButtonProps) {
  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        onToggle();
      }}
      disabled={loading}
      aria-pressed={isWatchlisted}
      aria-label={isWatchlisted ? "Retirer de ma liste" : "Ajouter à ma liste"}
      className={cn(
        "inline-flex items-center justify-center rounded-full p-1.5 text-sauge transition-colors hover:text-craie focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse disabled:cursor-not-allowed disabled:opacity-60",
        isWatchlisted && "text-pousse",
        className,
      )}
    >
      <Bookmark
        className="size-5"
        fill={isWatchlisted ? "currentColor" : "none"}
        aria-hidden="true"
      />
    </button>
  );
}

export { WatchlistButton };
