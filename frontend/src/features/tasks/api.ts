import { api } from "@/services/api"
import type { Paginated } from "@/types/api"
import type { Task } from "@/types/task"

export interface TaskListParams {
  page?: number
  page_size?: number
  search?: string
  status?: string
  priority?: string
  project?: string
  assignee?: string
  ordering?: string
}

export async function fetchTasks(
  params: TaskListParams = {},
): Promise<Paginated<Task>> {
  const { data } = await api.get<Paginated<Task>>("/tasks/", { params })
  return data
}

export async function fetchAllTasks(
  params: TaskListParams = {},
): Promise<Paginated<Task>> {
  const requestParams = { ...params, page_size: 200 }
  const { data } = await api.get<Paginated<Task>>("/tasks/", {
    params: requestParams,
  })
  return data
}

export async function fetchTask(id: string): Promise<Task> {
  const { data } = await api.get<Task>(`/tasks/${id}/`)
  return data
}

export interface CreateTaskPayload {
  title: string
  description?: string
  project?: string | null
  status?: string
  priority?: string
  assignee?: string | null
  due_date?: string | null
}

export async function createTask(
  payload: CreateTaskPayload,
): Promise<Task> {
  const { data } = await api.post<Task>("/tasks/", payload)
  return data
}

export async function updateTask(
  id: string,
  payload: Partial<CreateTaskPayload>,
): Promise<Task> {
  const { data } = await api.patch<Task>(`/tasks/${id}/`, payload)
  return data
}

export async function deleteTask(id: string): Promise<void> {
  await api.delete(`/tasks/${id}/`)
}

export async function changeTaskStatus(
  id: string,
  status: string,
): Promise<Task> {
  const { data } = await api.post<Task>(`/tasks/${id}/change-status/`, {
    status,
  })
  return data
}
