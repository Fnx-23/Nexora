import { api } from "@/services/api"
import type { Paginated } from "@/types/api"
import type { TimeEntry, TimeEntrySummary } from "@/types/timeEntry"

export interface TimeEntryListParams {
  page?: number
  page_size?: number
  project?: string
  user?: string
  date_from?: string
  date_to?: string
  ordering?: string
}

export async function fetchTimeEntries(
  params: TimeEntryListParams = {},
): Promise<Paginated<TimeEntry>> {
  const { data } = await api.get<Paginated<TimeEntry>>("/time-entries/", { params })
  return data
}

export async function fetchTimeEntry(id: string): Promise<TimeEntry> {
  const { data } = await api.get<TimeEntry>(`/time-entries/${id}/`)
  return data
}

export interface CreateTimeEntryPayload {
  project: string
  task?: string | null
  date: string
  start_time: string
  end_time?: string | null
  description?: string
}

export async function createTimeEntry(
  payload: CreateTimeEntryPayload,
): Promise<TimeEntry> {
  const { data } = await api.post<TimeEntry>("/time-entries/", payload)
  return data
}

export async function updateTimeEntry(
  id: string,
  payload: Partial<CreateTimeEntryPayload>,
): Promise<TimeEntry> {
  const { data } = await api.patch<TimeEntry>(`/time-entries/${id}/`, payload)
  return data
}

export async function deleteTimeEntry(id: string): Promise<void> {
  await api.delete(`/time-entries/${id}/`)
}

export async function fetchTimeEntrySummary(params: {
  date_from?: string
  date_to?: string
  project?: string
} = {}): Promise<TimeEntrySummary> {
  const { data } = await api.get<TimeEntrySummary>("/time-entries/summary/", { params })
  return data
}
