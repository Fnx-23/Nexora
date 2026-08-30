export type ProjectStatus =
  | "PLANNING"
  | "IN_PROGRESS"
  | "ON_HOLD"
  | "COMPLETED"
  | "ARCHIVED"

export type ProjectPriority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"

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
  created_at: string
  updated_at: string
}
