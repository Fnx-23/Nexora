import type { Activity, ActivityEntityType } from "@/types/activity"

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

export interface EntityMeta {
  label: string
  initial: string
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

export function entityMeta(entityType: string): EntityMeta {
  return ENTITY_META[entityType as ActivityEntityType] ?? FALLBACK_ENTITY_META
}

function asNonEmptyString(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null
}

function humanizeToken(value: unknown): string | null {
  const raw = asNonEmptyString(value)
  if (!raw) return null
  return raw.charAt(0).toUpperCase() + raw.slice(1).toLowerCase().replace(/_/g, " ")
}

function humanizeFieldName(field: string): string {
  return field.replace(/_id$/, "").replace(/_/g, " ")
}

export function activitySubject(activity: Activity): string {
  const meta = activity.metadata ?? {}
  return asNonEmptyString(meta.name) ?? asNonEmptyString(meta.title) ?? activity.action_display
}

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
    case "task.due_date_changed": {
      const from = asNonEmptyString(meta.old_due_date)
      const to = asNonEmptyString(meta.new_due_date)
      if (from && to) return `Due date ${from || "unset"} → ${to}`
      return to ? `Due ${to}` : null
    }
    case "task.attachment_added": {
      const name = asNonEmptyString(meta.original_filename)
      return name ? name : null
    }
    default:
      return null
  }
}

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
  { value: "project.member_added", label: "Member added to project" },
  { value: "project.member_removed", label: "Member removed from project" },
  { value: "task.created", label: "Task created" },
  { value: "task.assigned", label: "Task assigned" },
  { value: "task.status_changed", label: "Task status changed" },
  { value: "task.priority_changed", label: "Task priority changed" },
  { value: "task.due_date_changed", label: "Task due date changed" },
  { value: "task.comment_added", label: "Comment added to task" },
  { value: "task.comment_deleted", label: "Comment removed from task" },
  { value: "task.attachment_added", label: "Attachment added to task" },
  { value: "team.role_changed", label: "Team role changed" },
  { value: "password.changed", label: "Password changed" },
  { value: "password.reset", label: "Password reset" },
  { value: "email.verified", label: "Email verified" },
  { value: "session.revoked", label: "Session revoked" },
  { value: "sessions.revoked_others", label: "Sessions revoked" },
  { value: "profile.updated", label: "Profile updated" },
]
