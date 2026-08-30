export interface TimeEntry {
  id: string
  user: string
  user_name: string
  project: string
  project_name: string | null
  task: string | null
  task_title: string | null
  date: string
  start_time: string
  end_time: string | null
  duration: string | null
  description: string
  created_at: string
  updated_at: string
}

export interface TimeEntrySummary {
  total_entries: number
  total_duration_minutes: number
  by_project: Array<{
    project_name: string
    total_minutes: number
  }>
  by_date: Array<{
    date: string
    total_minutes: number
  }>
}
