import { Heart } from "lucide-react";
import { cn } from "../utils/cn";

interface LikeButtonProps {
  isLiked: boolean;
  likeCount: number;
  onToggle: () => void;
  loading?: boolean;
  className?: string;
}

// Likes a recipe and shows its public like count. Unlike WatchlistButton, this
// renders for anonymous visitors too — the count is public — with the click
// routed to /login by the parent when there's no session (see HomePage). The
// count is folded into the aria-label so screen readers announce it with the
// action; the visible number is aria-hidden to avoid a double read.
function LikeButton({ isLiked, likeCount, onToggle, loading = false, className }: LikeButtonProps) {
  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        onToggle();
      }}
      disabled={loading}
      aria-pressed={isLiked}
      aria-label={`${isLiked ? "Ne plus aimer" : "Aimer"} cette recette — ${likeCount} j'aime`}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-sauge transition-colors hover:text-craie focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse disabled:cursor-not-allowed disabled:opacity-60",
        isLiked && "text-pousse",
        className,
      )}
    >
      <Heart className="size-5" fill={isLiked ? "currentColor" : "none"} aria-hidden="true" />
      <span className="font-mono text-sm tabular-nums" aria-hidden="true">
        {likeCount}
      </span>
    </button>
  );
}

export { LikeButton };
