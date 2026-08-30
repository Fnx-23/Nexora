import type { ReactNode } from "react"

import { AlertTriangleIcon } from "@/components/icons"
import { Button } from "@/components/ui/Button"
import { cn } from "@/utils/cn"

export interface ErrorStateProps {
  title?: string
  description?: string
  onRetry?: () => void
  action?: ReactNode
  className?: string
}

export function ErrorState({
  title = "Something went wrong",
  description = "An unexpected error occurred. Please try again.",
  onRetry,
  action,
  className,
}: ErrorStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center px-6 py-20 text-center", className)}>
      <div className="flex size-14 items-center justify-center rounded-full bg-red-50 text-red-500">
        <AlertTriangleIcon className="size-7" />
      </div>
      <h3 className="mt-5 text-base font-semibold text-slate-900">{title}</h3>
      <p className="mt-1.5 max-w-sm text-sm text-slate-500">{description}</p>
      {(onRetry || action) && (
        <div className="mt-6">
          {action ?? (
            <Button variant="secondary" size="sm" onClick={onRetry}>
              Try again
            </Button>
          )}
        </div>
      )}
    </div>
  )
}
