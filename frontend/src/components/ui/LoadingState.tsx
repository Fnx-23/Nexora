import { cn } from "@/utils/cn"

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      role="status"
      aria-label="Loading"
      className={cn(
        "inline-block size-5 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600",
        className,
      )}
    />
  )
}

export interface LoadingStateProps {
  label?: string
  className?: string
}

export function LoadingState({ label = "Loading…", className }: LoadingStateProps) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-3 px-6 py-16", className)}>
      <Spinner />
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  )
}

/** Rectangular placeholder for skeleton layouts. */
export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn("animate-pulse rounded-md bg-slate-200", className)} />
}
