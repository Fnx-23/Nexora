
export type ActivityAction =
  | "customer.created"
  | "customer.updated"
  | "customer.archived"
  | "project.created"
  | "project.updated"
  | "project.status_changed"
  | "project.member_added"
  | "project.member_removed"
  | "task.created"
  | "task.assigned"
  | "task.status_changed"
  | "task.priority_changed"
  | "task.due_date_changed"
  | "task.comment_added"
  | "task.comment_deleted"
  | "task.attachment_added"
  | "team.role_changed"

export type ActivityEntityType = "customer" | "project" | "task" | "membership"

export interface Activity {
  id: string
  action: ActivityAction
  action_display: string
  entity_type: ActivityEntityType
  entity_id: string | null
  actor: string | null
  actor_name: string | null
  metadata: Record<string, unknown>
  timestamp: string
}
