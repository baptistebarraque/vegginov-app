import { type LucideIcon } from "lucide-react";
import { type ReactNode } from "react";
import { cn } from "../../utils/cn";

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

// Empty/error states state what happened and invite the next action; they do
// not apologise and are never vague (docs/FRONTEND.md §6.2 / §7).
function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-3 rounded-lg border border-dashed border-lisiere px-6 py-12 text-center",
        className,
      )}
    >
      {Icon && <Icon className="size-8 text-sauge" aria-hidden="true" />}
      <p className="font-display text-xl text-craie">{title}</p>
      {description && <p className="max-w-[46ch] text-sm text-sauge">{description}</p>}
      {action}
    </div>
  );
}

export { EmptyState };
