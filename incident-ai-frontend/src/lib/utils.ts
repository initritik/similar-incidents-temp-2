import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// shadcn/ui uses this helper to combine conditional classes safely while
// resolving Tailwind conflicts. That keeps reusable enterprise UI components
// predictable as variants and states grow.
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
