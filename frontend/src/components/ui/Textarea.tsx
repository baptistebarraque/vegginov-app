import { forwardRef, type TextareaHTMLAttributes } from "react";
import { cn } from "../../utils/cn";

const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea
      ref={ref}
      className={cn(
        "min-h-24 w-full rounded-md border border-lisiere bg-feuille-haut px-3 py-2 text-craie",
        "focus:border-pousse focus:ring-2 focus:ring-pousse/25 focus:outline-none",
        "disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      {...props}
    />
  ),
);
Textarea.displayName = "Textarea";

export { Textarea };
