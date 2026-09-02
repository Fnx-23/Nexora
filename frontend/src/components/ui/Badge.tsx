import type { HTMLAttributes } from "react"

import { cn } from "@/utils/cn"

type BadgeVariant =
  | "neutral"
  | "brand"
  | "success"
  | "warning"
  | "danger"
  | "info"

const variantClasses: Record<BadgeVariant, string> = {
  neutral: "bg-slate-100 text-slate-600",
  brand: "bg-brand-50 text-brand-700",
  success: "bg-emerald-50 text-emerald-700",
  warning: "bg-amber-50 text-amber-700",
  danger: "bg-red-50 text-red-700",
  info: "bg-sky-50 text-sky-700",
}

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
}

export function Badge({ variant = "neutral", className, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-lg px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
        variantClasses[variant],
        className,
      )}
      {...props}
    />
  )
}

const STATUS_VARIANTS: Record<string, BadgeVariant> = {
  ACTIVE: "success",
  COMPLETED: "info",
  IN_PROGRESS: "warning",
  TODO: "neutral",
  PLANNING: "info",
  ON_HOLD: "warning",
  CANCELLED: "danger",
  ARCHIVED: "neutral",
  DONE: "success",
  IN_REVIEW: "info",
  URGENT: "danger",
  HIGH: "warning",
  MEDIUM: "neutral",
  LOW: "neutral",
  ADMIN: "brand",
  MANAGER: "info",
  EMPLOYEE: "neutral",
}

export function StatusBadge({ value, className }: { value: string; className?: string }) {
  const variant = STATUS_VARIANTS[value] ?? "neutral"
  return (
    <Badge variant={variant} className={className}>
      {value.startsWith("ON_") ? value.slice(3) : value.replace("_", " ")}
    </Badge>
  )
}
