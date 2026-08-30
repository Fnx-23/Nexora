import type { ReactNode } from "react"

import { InboxIcon } from "@/components/icons"
import { cn } from "@/utils/cn"

export interface EmptyStateProps {
  title: string
  description?: string
  action?: ReactNode
  icon?: ReactNode
  className?: string
}

export function EmptyState({
  title,
  description,
  action,
  icon,
  className,
}: EmptyStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center px-6 py-20 text-center", className)}>
      <div className="flex size-14 items-center justify-center rounded-full bg-slate-100 text-slate-400">
        {icon ?? <InboxIcon className="size-7" />}
      </div>
      <h3 className="mt-5 text-base font-semibold text-slate-900">{title}</h3>
      {description && <p className="mt-1.5 max-w-sm text-sm text-slate-500">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
