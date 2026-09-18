/**
 * AI Study Companion — Utility Functions
 *
 * Shared utility functions used across the frontend.
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes with clsx for conditional classes.
 * Prevents conflicting utility classes.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a date string to a human-readable format.
 */
export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  // Less than 1 minute
  if (diff < 60 * 1000) return "Just now";

  // Less than 1 hour
  if (diff < 60 * 60 * 1000) {
    const mins = Math.floor(diff / (60 * 1000));
    return `${mins}m ago`;
  }

  // Less than 24 hours
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000));
    return `${hours}h ago`;
  }

  // Less than 7 days
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = Math.floor(diff / (24 * 60 * 60 * 1000));
    return `${days}d ago`;
  }

  // Otherwise show date
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
  });
}

/**
 * Format bytes to human-readable file size.
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Get mastery level label from score.
 */
export function getMasteryLevel(score: number): {
  label: string;
  color: string;
} {
  if (score >= 80) return { label: "Mastered", color: "#10B981" };
  if (score >= 60) return { label: "Proficient", color: "#6366F1" };
  if (score >= 40) return { label: "Developing", color: "#F59E0B" };
  return { label: "Beginning", color: "#EF4444" };
}

/**
 * Get trend icon and color.
 */
export function getTrendInfo(trend: string): {
  icon: string;
  color: string;
  label: string;
} {
  switch (trend) {
    case "improving":
      return { icon: "↑", color: "#10B981", label: "Improving" };
    case "declining":
      return { icon: "↓", color: "#EF4444", label: "Declining" };
    case "stable":
      return { icon: "→", color: "#6B7280", label: "Stable" };
    default:
      return { icon: "•", color: "#9CA3AF", label: "New" };
  }
}

/**
 * Truncate text to a max length with ellipsis.
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + "...";
}
