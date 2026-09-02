import { api } from "@/services/api"
import type { Paginated } from "@/types/api"
import type {
  Task,
  TaskChecklistItem,
  TaskComment,
  TaskDetail,
  TaskLabel,
  TaskSubtask,
} from "@/types/task"

export interface TaskListParams {
  page?: number
  page_size?: number
  search?: string
  status?: string
  priority?: string
  project?: string
  assignee?: string
  label?: string
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

export async function fetchTask(id: string): Promise<TaskDetail> {
  const { data } = await api.get<TaskDetail>(`/tasks/${id}/`)
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
  label_ids?: string[]
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

export async function fetchTaskComments(id: string): Promise<TaskComment[]> {
  const { data } = await api.get<TaskComment[]>(`/tasks/${id}/comments/`)
  return data
}

export async function addTaskComment(
  id: string,
  body: string,
): Promise<TaskComment> {
  const { data } = await api.post<TaskComment>(`/tasks/${id}/comments/`, { body })
  return data
}

export async function updateTaskComment(
  id: string,
  commentId: string,
  body: string,
): Promise<TaskComment> {
  const { data } = await api.patch<TaskComment>(
    `/tasks/${id}/comments/${commentId}/`,
    { body },
  )
  return data
}

export async function deleteTaskComment(id: string, commentId: string): Promise<void> {
  await api.delete(`/tasks/${id}/comments/${commentId}/`)
}

export async function fetchTaskChecklist(id: string): Promise<TaskChecklistItem[]> {
  const { data } = await api.get<TaskChecklistItem[]>(`/tasks/${id}/checklist/`)
  return data
}

export async function addTaskChecklistItem(
  id: string,
  text: string,
): Promise<TaskChecklistItem> {
  const { data } = await api.post<TaskChecklistItem>(`/tasks/${id}/checklist/`, { text })
  return data
}

export async function updateTaskChecklistItem(
  id: string,
  itemId: string,
  payload: Partial<Pick<TaskChecklistItem, "text" | "completed">>,
): Promise<TaskChecklistItem> {
  const { data } = await api.patch<TaskChecklistItem>(
    `/tasks/${id}/checklist/${itemId}/`,
    payload,
  )
  return data
}

export async function deleteTaskChecklistItem(id: string, itemId: string): Promise<void> {
  await api.delete(`/tasks/${id}/checklist/${itemId}/`)
}

export async function fetchTaskSubtasks(id: string): Promise<TaskSubtask[]> {
  const { data } = await api.get<TaskSubtask[]>(`/tasks/${id}/subtasks/`)
  return data
}

export async function addTaskSubtask(id: string, title: string): Promise<TaskSubtask> {
  const { data } = await api.post<TaskSubtask>(`/tasks/${id}/subtasks/`, { title })
  return data
}

export async function updateTaskSubtask(
  id: string,
  subtaskId: string,
  payload: Partial<Pick<TaskSubtask, "title" | "completed">>,
): Promise<TaskSubtask> {
  const { data } = await api.patch<TaskSubtask>(
    `/tasks/${id}/subtasks/${subtaskId}/`,
    payload,
  )
  return data
}

export async function deleteTaskSubtask(id: string, subtaskId: string): Promise<void> {
  await api.delete(`/tasks/${id}/subtasks/${subtaskId}/`)
}

export interface CreateLabelPayload {
  name: string
  color?: string
}

export async function fetchLabels(
  params: { page_size?: number } = {},
): Promise<Paginated<TaskLabel>> {
  const { data } = await api.get<Paginated<TaskLabel>>("/labels/", { params })
  return data
}

export async function createLabel(payload: CreateLabelPayload): Promise<TaskLabel> {
  const { data } = await api.post<TaskLabel>("/labels/", payload)
  return data
}

export async function updateLabel(
  id: string,
  payload: Partial<CreateLabelPayload>,
): Promise<TaskLabel> {
  const { data } = await api.patch<TaskLabel>(`/labels/${id}/`, payload)
  return data
}

export async function deleteLabel(id: string): Promise<void> {
  await api.delete(`/labels/${id}/`)
}