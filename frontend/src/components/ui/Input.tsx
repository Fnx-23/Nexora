import { forwardRef, useId, type InputHTMLAttributes } from "react"

import { cn } from "@/utils/cn"

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { label, error, hint, className, id, ...props },
  ref,
) {
  const autoId = useId()
  const inputId = id ?? autoId

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="mb-1.5 block text-sm font-medium text-slate-700">
          {label}
        </label>
      )}
      <input
        ref={ref}
        id={inputId}
        aria-invalid={Boolean(error) || undefined}
        aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
        className={cn(
          "block h-10 w-full rounded-lg border bg-white px-3 text-sm shadow-sm",
          "placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-offset-0",
          error
            ? "border-red-300 focus:border-red-500 focus:ring-red-500"
            : "border-slate-300 focus:border-brand-500 focus:ring-brand-500",
          className,
        )}
        {...props}
      />
      {error && (
        <p id={`${inputId}-error`} role="alert" className="mt-1.5 text-sm text-red-600">
          {error}
        </p>
      )}
      {!error && hint && (
        <p id={`${inputId}-hint`} className="mt-1.5 text-sm text-slate-500">
          {hint}
        </p>
      )}
    </div>
  )
})
