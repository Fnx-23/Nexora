import type { Activity, ActivityEntityType } from "@/types/activity"

/* -------------------------------------------------------------------------- */
/* Time                                                                       */
/* -------------------------------------------------------------------------- */

/** Compact relative-time label, e.g. "Just now", "3m ago", "2h ago", "5d ago". */
export function timeAgo(isoDate: string): string {
  const then = new Date(isoDate).getTime()
  if (Number.isNaN(then)) return ""
  const diffMin = Math.floor((Date.now() - then) / 60_000)
  if (diffMin < 1) return "Just now"
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.floor(diffHr / 24)
  if (diffDay < 30) return `${diffDay}d ago`
  const diffMonth = Math.floor(diffDay / 30)
  return `${diffMonth}mo ago`
}

/** Absolute, human timestamp for tooltips and full display. */
export function formatTimestamp(isoDate: string): string {
  const date = new Date(isoDate)
  if (Number.isNaN(date.getTime())) return ""
  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

/* -------------------------------------------------------------------------- */
/* Entity presentation                                                        */
/* -------------------------------------------------------------------------- */

export interface EntityMeta {
  label: string
  /** Single-character glyph for the row avatar. */
  initial: string
  /** Tailwind color classes for the row avatar. */
  className: string
}

const ENTITY_META: Record<ActivityEntityType, EntityMeta> = {
  customer: { label: "Customer", initial: "C", className: "bg-brand-50 text-brand-700" },
  project: { label: "Project", initial: "P", className: "bg-sky-50 text-sky-700" },
  task: { label: "Task", initial: "T", className: "bg-emerald-50 text-emerald-700" },
  membership: { label: "Team", initial: "M", className: "bg-amber-50 text-amber-700" },
}

const FALLBACK_ENTITY_META: EntityMeta = {
  label: "Activity",
  initial: "•",
  className: "bg-slate-100 text-slate-600",
}

/** Presentation metadata for an entity type, with a safe fallback for unknown types. */
export function entityMeta(entityType: string): EntityMeta {
  return ENTITY_META[entityType as ActivityEntityType] ?? FALLBACK_ENTITY_META
}

/* -------------------------------------------------------------------------- */
/* Activity description                                                       */
/* -------------------------------------------------------------------------- */

function asNonEmptyString(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null
}

/** "IN_PROGRESS" -> "In progress", "TODO" -> "Todo", "ON_HOLD" -> "On hold". */
function humanizeToken(value: unknown): string | null {
  const raw = asNonEmptyString(value)
  if (!raw) return null
  return raw.charAt(0).toUpperCase() + raw.slice(1).toLowerCase().replace(/_/g, " ")
}

/** "assignee_id" -> "assignee", "start_date" -> "start date". */
function humanizeFieldName(field: string): string {
  return field.replace(/_id$/, "").replace(/_/g, " ")
}

/**
 * The primary subject of an activity — the affected object's name/title from
 * (sanitized) metadata, falling back to the human action label.
 */
export function activitySubject(activity: Activity): string {
  const meta = activity.metadata ?? {}
  return asNonEmptyString(meta.name) ?? asNonEmptyString(meta.title) ?? activity.action_display
}

/**
 * A short, human detail line derived from the sanitized metadata (a status
 * transition, the fields that changed, ...), or `null` when nothing to add.
 * Robust to unknown/missing metadata shapes.
 */
export function activityDetail(activity: Activity): string | null {
  const meta = activity.metadata ?? {}

  switch (activity.action) {
    case "project.status_changed":
    case "task.status_changed": {
      const from = humanizeToken(meta.old_status)
      const to = humanizeToken(meta.new_status)
      if (from && to) return `${from} → ${to}`
      return to ? `Set to ${to}` : null
    }
    case "team.role_changed": {
      const from = humanizeToken(meta.old_role)
      const to = humanizeToken(meta.new_role)
      if (from && to) return `${from} → ${to}`
      return to ? `Set to ${to}` : null
    }
    case "customer.updated":
    case "project.updated": {
      const fields = Array.isArray(meta.changed_fields)
        ? meta.changed_fields.filter((f): f is string => typeof f === "string")
        : []
      if (fields.length === 0) return null
      return `Changed ${fields.map(humanizeFieldName).join(", ")}`
    }
    case "task.assigned": {
      const to = asNonEmptyString(meta.new_assignee_id)
      const from = asNonEmptyString(meta.old_assignee_id)
      if (!to) return "Unassigned"
      return from ? "Reassigned" : "Assigned"
    }
    default:
      return null
  }
}

/* -------------------------------------------------------------------------- */
/* Filter option lists (for the Activity page)                                */
/* -------------------------------------------------------------------------- */

export const ENTITY_TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All types" },
  { value: "customer", label: "Customers" },
  { value: "project", label: "Projects" },
  { value: "task", label: "Tasks" },
  { value: "membership", label: "Team" },
]

export const ACTION_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All activity" },
  { value: "customer.created", label: "Customer created" },
  { value: "customer.updated", label: "Customer updated" },
  { value: "customer.archived", label: "Customer archived" },
  { value: "project.created", label: "Project created" },
  { value: "project.updated", label: "Project updated" },
  { value: "project.status_changed", label: "Project status changed" },
  { value: "task.created", label: "Task created" },
  { value: "task.assigned", label: "Task assigned" },
  { value: "task.status_changed", label: "Task status changed" },
  { value: "team.role_changed", label: "Team role changed" },
]
