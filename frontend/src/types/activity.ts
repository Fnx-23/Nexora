/** Types for the tenant-scoped audit log, mirroring the backend ActivitySerializer. */

/** The catalogue of audited business events (matches `ActivityAction` on the server). */
export type ActivityAction =
  | "customer.created"
  | "customer.updated"
  | "customer.archived"
  | "project.created"
  | "project.updated"
  | "project.status_changed"
  | "task.created"
  | "task.assigned"
  | "task.status_changed"
  | "team.role_changed"

/** The kind of object an activity refers to. */
export type ActivityEntityType = "customer" | "project" | "task" | "membership"

/** A single append-only audit-log entry. */
export interface Activity {
  id: string
  action: ActivityAction
  /** Human-readable label for `action`, e.g. "Customer created". */
  action_display: string
  entity_type: ActivityEntityType
  /** UUID of the affected object; null when it was not recorded. */
  entity_id: string | null
  /** UUID of the acting user; null for system actions. */
  actor: string | null
  /** Full name or email of the actor; null for system actions. */
  actor_name: string | null
  /** Non-sensitive contextual detail (sanitized server-side). Shape varies by action. */
  metadata: Record<string, unknown>
  /** ISO-8601 timestamp of when the event occurred. */
  timestamp: string
}
