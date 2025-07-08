import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const userFeatureToggle = {
  PUSH_TO_MARKETPLACE: 'push_to_marketplace',
} as const;
