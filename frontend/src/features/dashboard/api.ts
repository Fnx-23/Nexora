import { api } from "@/services/api"

export interface DashboardKPIs {
  active_projects: number
  total_projects: number
  total_customers: number
  open_tasks: number
  overdue_tasks: number
  completed_tasks: number
  total_tasks: number
  team_members: number
}

export interface StatusCount {
  status: string
  label: string
  count: number
}

export interface RecentProject {
  id: string
  name: string
  status: string
  priority: string
  deadline: string | null
  updated_at: string
}

export interface RecentTask {
  id: string
  title: string
  status: string
  priority: string
  assignee_name: string | null
  due_date: string | null
  updated_at: string
}

export interface ActivityItem {
  type: "project" | "task"
  id: string
  name: string
  status: string
  updated_at: string
}

export interface DashboardData {
  kpis: DashboardKPIs
  project_status_distribution: StatusCount[]
  task_status_distribution: StatusCount[]
  recent_projects: RecentProject[]
  recent_tasks: RecentTask[]
  activity: ActivityItem[]
}

export async function fetchDashboard(): Promise<DashboardData> {
  const { data } = await api.get<DashboardData>("/dashboard/")
  return data
}
