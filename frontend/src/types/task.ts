export type TaskStatus = "TODO" | "IN_PROGRESS" | "IN_REVIEW" | "DONE" | "CANCELLED"
export type TaskPriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT"

export interface TaskLabel {
  id: string
  name: string
  color: string
  created_at: string
}

export interface TaskComment {
  id: string
  task: string
  author: string | null
  author_name: string | null
  body: string
  created_at: string
  updated_at: string
}

export interface TaskChecklistItem {
  id: string
  task: string
  text: string
  completed: boolean
  position: number
  created_at: string
}

export interface TaskSubtask {
  id: string
  task: string
  title: string
  completed: boolean
  position: number
  created_at: string
}

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
  labels: TaskLabel[]
  checklist_total: number
  checklist_done: number
  subtask_total: number
  subtask_done: number
  comments_count: number
  created_at: string
  updated_at: string
}

export interface TaskDetail extends Task {
  recent_activity: import("@/types/activity").Activity[]
}

export const KANBAN_COLUMNS: TaskStatus[] = ["TODO", "IN_PROGRESS", "IN_REVIEW", "DONE"]

export const KANBAN_COLUMN_LABELS: Record<TaskStatus, string> = {
  TODO: "To Do",
  IN_PROGRESS: "In Progress",
  IN_REVIEW: "In Review",
  DONE: "Done",
  CANCELLED: "Cancelled",
}