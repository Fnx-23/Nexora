export interface Notification {
  id: string
  verb: string
  entity_type: string
  entity_id: string | null
  entity_name: string
  link: string
  is_read: boolean
  category: string
  actor_name: string
  created_at: string
}

export interface NotificationPreference {
  id: string
  task_assigned: boolean
  task_due_soon: boolean
  task_overdue: boolean
  task_comment: boolean
  project_assigned: boolean
  project_deadline: boolean
  invitation_received: boolean
  role_changed: boolean
  email_task_assigned: boolean
  email_task_due_soon: boolean
  email_task_overdue: boolean
  email_task_comment: boolean
  email_project_assigned: boolean
  email_project_deadline: boolean
  email_invitation_received: boolean
  email_role_changed: boolean
}

export type NotificationPreferenceKey =
  | "task_assigned"
  | "task_due_soon"
  | "task_overdue"
  | "task_comment"
  | "project_assigned"
  | "project_deadline"
  | "invitation_received"
  | "role_changed"
  | "email_task_assigned"
  | "email_task_due_soon"
  | "email_task_overdue"
  | "email_task_comment"
  | "email_project_assigned"
  | "email_project_deadline"
  | "email_invitation_received"
  | "email_role_changed"

export interface UnreadCountResponse {
  count: number
}

export interface MarkAllReadResponse {
  updated: number
}