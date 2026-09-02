import { useMemo } from "react"
import { cn } from "@/utils/cn"

export function ProgressBar({
  value,
  max = 100,
  showLabel = true,
  className,
}: {
  value: number
  max?: number
  showLabel?: boolean
  className?: string
}) {
  const percentage = Math.min(Math.max(Math.round((value / max) * 100), 0), 100)

  const colorClass =
    percentage >= 100
      ? "bg-emerald-500"
      : percentage >= 60
        ? "bg-brand-500"
        : percentage >= 30
          ? "bg-amber-500"
          : "bg-slate-400"

  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <div className="h-2 w-full flex-1 overflow-hidden rounded-full bg-slate-100">
        <div
          className={cn("h-full rounded-full transition-all duration-300", colorClass)}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <span className="w-10 text-right text-xs font-semibold tabular-nums text-slate-700">
          {percentage}%
        </span>
      )}
    </div>
  )
}

export interface ComparisonBarItem {
  id: string
  label: string
  sublabel?: string
  value: number
  formattedValue: string
  color?: string
}

export function HorizontalBarChart({
  items,
  emptyMessage = "No data available.",
  maxItems = 6,
}: {
  items: ComparisonBarItem[]
  emptyMessage?: string
  maxItems?: number
}) {
  const displayItems = useMemo(() => items.slice(0, maxItems), [items, maxItems])
  const maxValue = useMemo(() => {
    const max = Math.max(...displayItems.map((i) => i.value), 0)
    return max === 0 ? 1 : max
  }, [displayItems])

  if (displayItems.length === 0 || displayItems.every((i) => i.value === 0)) {
    return (
      <div className="flex h-36 items-center justify-center text-sm text-slate-500">
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className="space-y-3.5">
      {displayItems.map((item) => {
        const widthPct = Math.max(Math.round((item.value / maxValue) * 100), 2)
        return (
          <div key={item.id} className="space-y-1">
            <div className="flex items-center justify-between text-xs font-medium">
              <div className="flex min-w-0 items-center gap-2">
                <span className="truncate text-slate-800">{item.label}</span>
                {item.sublabel && (
                  <span className="truncate text-[11px] text-slate-600 font-normal">
                    ({item.sublabel})
                  </span>
                )}
              </div>
              <span className="ml-2 shrink-0 tabular-nums font-semibold text-slate-900">
                {item.formattedValue}
              </span>
            </div>
            <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-300",
                  item.color || "bg-brand-500",
                )}
                style={{ width: `${widthPct}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function WorkloadStackedBar({
  completed,
  open,
  overdue,
}: {
  completed: number
  open: number
  overdue: number
}) {
  const total = completed + open
  if (total === 0) {
    return <span className="text-xs text-slate-500">No tasks</span>
  }

  const completedPct = Math.round((completed / total) * 100)
  const regularOpen = Math.max(open - overdue, 0)
  const regularOpenPct = Math.round((regularOpen / total) * 100)
  const overduePct = Math.max(100 - completedPct - regularOpenPct, 0)

  return (
    <div className="space-y-1.5">
      <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
        {completed > 0 && (
          <div
            className="h-full bg-emerald-500"
            style={{ width: `${completedPct}%` }}
            title={`Completed: ${completed}`}
          />
        )}
        {regularOpen > 0 && (
          <div
            className="h-full bg-sky-400"
            style={{ width: `${regularOpenPct}%` }}
            title={`Open: ${regularOpen}`}
          />
        )}
        {overdue > 0 && (
          <div
            className="h-full bg-rose-500"
            style={{ width: `${overduePct}%` }}
            title={`Overdue: ${overdue}`}
          />
        )}
      </div>
      <div className="flex items-center gap-3 text-[11px] text-slate-600">
        <span className="flex items-center gap-1 font-medium">
          <span className="size-2 rounded-full bg-emerald-500" />
          {completed} done
        </span>
        <span className="flex items-center gap-1 font-medium">
          <span className="size-2 rounded-full bg-sky-400" />
          {open} open
        </span>
        {overdue > 0 && (
          <span className="flex items-center gap-1 font-semibold text-rose-600">
            <span className="size-2 rounded-full bg-rose-500" />
            {overdue} overdue
          </span>
        )}
      </div>
    </div>
  )
}

export interface TimelineItem {
  date: string
  hours: number
  entry_count: number
}

export function TimelineChart({
  items,
  emptyMessage = "No tracked time in this period.",
}: {
  items: TimelineItem[]
  emptyMessage?: string
}) {
  const maxHours = useMemo(() => {
    const max = Math.max(...items.map((i) => i.hours), 0)
    return max === 0 ? 1 : max
  }, [items])

  if (items.length === 0 || items.every((i) => i.hours === 0)) {
    return (
      <div className="flex h-44 items-center justify-center text-sm text-slate-500">
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex h-36 items-end gap-2 border-b border-slate-200 pb-2">
        {items.map((item) => {
          const heightPct = Math.max(Math.round((item.hours / maxHours) * 100), 4)
          const formattedDate = new Date(item.date + "T00:00:00").toLocaleDateString(
            "en",
            { month: "short", day: "numeric" },
          )
          return (
            <div
              key={item.date}
              className="group relative flex flex-1 flex-col items-center justify-end"
            >
              <div className="pointer-events-none absolute -top-9 z-20 hidden rounded-md bg-slate-900 px-2 py-1 text-[10px] font-medium text-white shadow-sm group-hover:block whitespace-nowrap">
                {item.hours}h ({item.entry_count} entries)
              </div>
              <div
                className={cn(
                  "w-full max-w-[32px] rounded-t-sm transition-all duration-200",
                  item.hours > 0
                    ? "bg-brand-500 hover:bg-brand-600"
                    : "bg-slate-200",
                )}
                style={{ height: `${heightPct}%` }}
              />
              <span className="mt-1.5 hidden truncate text-[10px] text-slate-600 md:block">
                {formattedDate}
              </span>
            </div>
          )
        })}
      </div>
      <div className="flex justify-between text-[11px] text-slate-600">
        <span>{items[0]?.date}</span>
        <span>Peak: {maxHours.toFixed(1)} hrs/day</span>
        <span>{items[items.length - 1]?.date}</span>
      </div>
    </div>
  )
}

export interface DistributionSegment {
  key: string
  label: string
  value: number
  percentage: number
  colorClass: string
}

export function DistributionBar({
  segments,
  emptyMessage = "No data to distribute.",
}: {
  segments: DistributionSegment[]
  emptyMessage?: string
}) {
  const activeSegments = segments.filter((s) => s.value > 0)
  if (activeSegments.length === 0) {
    return (
      <div className="py-4 text-center text-sm text-slate-500">{emptyMessage}</div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-slate-100">
        {activeSegments.map((s) => (
          <div
            key={s.key}
            className={cn("h-full transition-all duration-200", s.colorClass)}
            style={{ width: `${s.percentage}%` }}
            title={`${s.label}: ${s.value} (${s.percentage}%)`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-slate-600">
        {activeSegments.map((s) => (
          <span key={s.key} className="flex items-center gap-1.5">
            <span className={cn("size-2.5 rounded-sm", s.colorClass)} />
            <span className="font-medium text-slate-700">{s.label}:</span>
            <span className="tabular-nums font-semibold text-slate-900">
              {s.value} ({s.percentage}%)
            </span>
          </span>
        ))}
      </div>
    </div>
  )
}
