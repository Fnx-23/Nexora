import { forwardRef, useId, type SelectHTMLAttributes } from "react"

import { ChevronDownIcon } from "@/components/icons"
import { cn } from "@/utils/cn"

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { label, error, className, children, id, ...props },
  ref,
) {
  const autoId = useId()
  const selectId = id ?? autoId

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={selectId} className="mb-1.5 block text-sm font-medium text-slate-700">
          {label}
        </label>
      )}
      <div className="relative">
        <select
          ref={ref}
          id={selectId}
          aria-invalid={Boolean(error) || undefined}
          className={cn(
            "block h-10 w-full appearance-none rounded-lg border bg-white px-3 pr-9 text-sm transition-colors",
            "focus:outline-none",
            error
              ? "border-red-300 focus:border-red-500 focus:ring-2 focus:ring-red-500/20"
              : "border-slate-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20",
            className,
          )}
          {...props}
        >
          {children}
        </select>
        <ChevronDownIcon className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-slate-400" />
      </div>
      {error && (
        <p role="alert" className="mt-1.5 text-xs text-red-600">
          {error}
        </p>
      )}
    </div>
  )
})
