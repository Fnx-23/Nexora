import type { Activity } from "@/types/activity"

export type ProjectStatus =
  | "PLANNING"
  | "IN_PROGRESS"
  | "ON_HOLD"
  | "COMPLETED"
  | "ARCHIVED"

export type ProjectPriority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"

export type ProjectHealth = "NOT_STARTED" | "ON_TRACK" | "AT_RISK" | "OVERDUE" | "COMPLETED"

export interface ProjectMember {
  id: string
  project: string
  user: string
  email: string
  full_name: string
  avatar: string | null
  created_at: string
}

export interface Project {
  id: string
  name: string
  description: string
  customer: string | null
  customer_name: string | null
  manager: string | null
  manager_name: string | null
  status: ProjectStatus
  priority: ProjectPriority
  start_date: string | null
  deadline: string | null
  progress?: number
  health?: ProjectHealth
  task_count?: number
  done_count?: number
  in_progress_count?: number
  todo_count?: number
  overdue_count?: number
  tracked_hours?: number
  member_count?: number
  members?: ProjectMember[]
  recent_activity?: Activity[]
  created_at: string
  updated_at: string
}

export const PROJECT_HEALTH_LABELS: Record<ProjectHealth, string> = {
  NOT_STARTED: "Not started",
  ON_TRACK: "On track",
  AT_RISK: "At risk",
  OVERDUE: "Overdue",
  COMPLETED: "Completed",
}
