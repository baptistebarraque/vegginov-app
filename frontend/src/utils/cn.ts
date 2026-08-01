import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// Compose conditional Tailwind classes: clsx resolves the conditionals, then
// tailwind-merge dedupes conflicting utilities so the last one wins.
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
