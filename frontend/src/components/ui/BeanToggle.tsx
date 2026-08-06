import { Bean } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "../../utils/cn";

interface BeanToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  className?: string;
}

// On/off switch shaped like a bean pod: the bean slides between the two ends
// of the pill track and fills solid when "on", echoing WatchlistButton's
// pressed/filled icon convention but as a slider rather than a static icon.
function BeanToggle({ checked, onChange, label, className }: BeanToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={cn(
        "inline-flex items-center gap-3 rounded-full focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pousse",
        className,
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "relative flex h-7 w-12 shrink-0 items-center rounded-full border transition-colors duration-200",
          checked ? "border-pousse bg-pousse-sourd/40" : "border-lisiere bg-feuille-haut",
        )}
      >
        <motion.span
          animate={{ x: checked ? 20 : 0 }}
          transition={{ type: "spring", stiffness: 500, damping: 32 }}
          className="absolute left-0.5 flex size-6 items-center justify-center rounded-full"
        >
          <Bean
            className={cn("size-5 transition-colors", checked ? "text-pousse" : "text-sauge")}
            fill={checked ? "currentColor" : "none"}
          />
        </motion.span>
      </span>
      <span className="text-sm text-sauge">{label}</span>
    </button>
  );
}

export { BeanToggle };
