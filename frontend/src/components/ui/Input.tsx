import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "../../utils/cn";

// Inputs sit on feuille-haut with a lisiere border; focus moves the border to
// pousse plus a 2px outer ring at 25% opacity (docs/FRONTEND.md §6.1).
const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-10 w-full rounded-md border border-lisiere bg-feuille-haut px-3 text-craie",
        "focus:border-pousse focus:ring-2 focus:ring-pousse/25 focus:outline-none",
        "disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";

export { Input };
