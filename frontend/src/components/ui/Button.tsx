import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react"

import { cn } from "@/utils/cn"

type Variant = "primary" | "secondary" | "ghost" | "danger"
type Size = "sm" | "md" | "lg"

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  isLoading?: boolean
  leftIcon?: ReactNode
}

const variantClasses: Record<Variant, string> = {
  primary:
    "bg-brand-600 text-white shadow-sm hover:bg-brand-700 focus-visible:ring-brand-600 active:bg-brand-800 disabled:bg-brand-400",
  secondary:
    "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 hover:border-slate-300 focus-visible:ring-brand-600 active:bg-slate-100",
  ghost: "text-slate-600 hover:bg-slate-100 hover:text-slate-900 focus-visible:ring-slate-400 active:bg-slate-200",
  danger:
    "bg-red-600 text-white shadow-sm hover:bg-red-700 focus-visible:ring-red-600 active:bg-red-800",
}

const sizeClasses: Record<Size, string> = {
  sm: "h-8 gap-1.5 rounded-lg px-3.5 text-sm font-medium",
  md: "h-10 gap-2 rounded-lg px-4 text-sm font-medium",
  lg: "h-11 gap-2.5 rounded-lg px-5 text-sm font-medium",
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", size = "md", isLoading = false, leftIcon, className, children, disabled, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled || isLoading}
      className={cn(
        "inline-flex items-center justify-center transition-all duration-150",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed",
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    >
      {isLoading ? (
        <span
          aria-hidden="true"
          className="size-3.5 shrink-0 animate-spin rounded-full border-2 border-current border-t-transparent"
        />
      ) : (
        leftIcon
      )}
      {children}
    </button>
  )
})
