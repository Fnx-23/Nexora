export type ReportType =
  | "project-performance"
  | "team-workload"
  | "time"
  | "customer-overview"

export interface ReportFilterParams {
  date_from?: string
  date_to?: string
  project?: string
  user?: string
  customer?: string
  status?: string
}


export interface ProjectPerformanceItem {
  project_id: string
  project_name: string
  status: string
  status_label: string
  priority: string
  progress: number
  completed_tasks: number
  open_tasks: number
  total_tasks: number
  overdue_tasks: number
  tracked_hours: number
  customer_id: string | null
  customer_name: string | null
  manager_name: string | null
  start_date: string | null
  deadline: string | null
}

export interface ProjectPerformanceSummary {
  total_projects: number
  total_tracked_hours: number
  average_progress: number
  total_tasks: number
  total_completed_tasks: number
  total_open_tasks: number
  total_overdue_tasks: number
}

export interface ProjectStatusDistItem {
  status: string
  label: string
  count: number
}

export interface ProjectPerformanceReport {
  summary: ProjectPerformanceSummary
  status_distribution: ProjectStatusDistItem[]
  results: ProjectPerformanceItem[]
}


export interface TeamWorkloadItem {
  user_id: string
  name: string
  email: string
  role: string
  assigned_tasks: number
  open_tasks: number
  completed_tasks: number
  overdue_tasks: number
  tracked_hours: number
  completion_rate: number
}

export interface TeamWorkloadSummary {
  total_members: number
  total_assigned_tasks: number
  total_open_tasks: number
  total_completed_tasks: number
  total_overdue_tasks: number
  total_tracked_hours: number
  overall_completion_rate: number
}

export interface TeamWorkloadReport {
  summary: TeamWorkloadSummary
  results: TeamWorkloadItem[]
}


export interface TimeReportProjectItem {
  project_id: string
  project_name: string
  customer_name: string
  hours: number
  entry_count: number
  percentage: number
}

export interface TimeReportUserItem {
  user_id: string
  user_name: string
  email: string
  hours: number
  entry_count: number
  percentage: number
}

export interface TimeReportTimelineItem {
  date: string
  hours: number
  entry_count: number
}

export interface TimeReportEntryItem {
  id: string
  date: string
  project_id: string
  project_name: string
  user_id: string
  user_name: string
  task_id: string | null
  task_title: string | null
  duration_hours: number
  start_time: string | null
  end_time: string | null
  description: string
}

export interface TimeReportSummary {
  total_hours: number
  total_entries: number
  active_projects_count: number
  active_users_count: number
  days_with_activity: number
  avg_daily_hours: number
}

export interface TimeReport {
  summary: TimeReportSummary
  hours_by_project: TimeReportProjectItem[]
  hours_by_user: TimeReportUserItem[]
  timeline: TimeReportTimelineItem[]
  entries: TimeReportEntryItem[]
}


export interface CustomerOverviewItem {
  customer_id: string
  customer_name: string
  company_name: string
  display_name: string
  email: string
  phone: string
  status: string
  is_active: boolean
  active_projects: number
  completed_projects: number
  total_projects: number
  open_tasks: number
  hours_tracked: number
}

export interface CustomerOverviewSummary {
  total_customers: number
  active_customers: number
  total_active_projects: number
  total_completed_projects: number
  total_tracked_hours: number
}

export interface CustomerOverviewReport {
  summary: CustomerOverviewSummary
  results: CustomerOverviewItem[]
}


export interface ExecutiveSummaryReport {
  project_performance: ProjectPerformanceSummary
  team_workload: TeamWorkloadSummary
  time_report: TimeReportSummary
  customer_overview: CustomerOverviewSummary
}
