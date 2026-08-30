export type TaskStatus = "TODO" | "IN_PROGRESS" | "IN_REVIEW" | "DONE" | "CANCELLED"
export type TaskPriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT"

export interface Task {
  id: string
  title: string
  description: string
  project: string | null
  project_name: string | null
  status: TaskStatus
  priority: TaskPriority
  assignee: string | null
  assignee_name: string | null
  created_by: string | null
  created_by_name: string | null
  due_date: string | null
  created_at: string
  updated_at: string
}

export const KANBAN_COLUMNS: TaskStatus[] = ["TODO", "IN_PROGRESS", "IN_REVIEW", "DONE"]

export const KANBAN_COLUMN_LABELS: Record<TaskStatus, string> = {
  TODO: "To Do",
  IN_PROGRESS: "In Progress",
  IN_REVIEW: "In Review",
  DONE: "Done",
  CANCELLED: "Cancelled",
}
