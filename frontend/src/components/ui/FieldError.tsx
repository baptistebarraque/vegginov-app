import { type HTMLAttributes } from "react";
import { cn } from "../../utils/cn";

// Inline validation message under a field. Renders nothing when empty so it
// never reserves space; announced politely when it appears (docs/FRONTEND.md §7).
function FieldError({ children, className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  if (!children) {
    return null;
  }
  return (
    <p aria-live="polite" className={cn("text-sm text-brique", className)} {...props}>
      {children}
    </p>
  );
}

export { FieldError };
