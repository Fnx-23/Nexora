import { api } from "@/services/api"
import type { Paginated } from "@/types/api"
import type { Project, ProjectMember } from "@/types/project"

export interface ProjectListParams {
  page?: number
  page_size?: number
  search?: string
  status?: string
  priority?: string
  customer?: string
  ordering?: string
}

export async function fetchProjects(
  params: ProjectListParams = {},
): Promise<Paginated<Project>> {
  const { data } = await api.get<Paginated<Project>>("/projects/", { params })
  return data
}

export async function fetchProject(id: string): Promise<Project> {
  const { data } = await api.get<Project>(`/projects/${id}/`)
  return data
}

export interface CreateProjectPayload {
  name: string
  description?: string
  customer?: string | null
  manager?: string | null
  status?: string
  priority?: string
  start_date?: string | null
  deadline?: string | null
}

export async function createProject(
  payload: CreateProjectPayload,
): Promise<Project> {
  const { data } = await api.post<Project>("/projects/", payload)
  return data
}

export async function updateProject(
  id: string,
  payload: Partial<CreateProjectPayload>,
): Promise<Project> {
  const { data } = await api.patch<Project>(`/projects/${id}/`, payload)
  return data
}

export async function archiveProject(id: string): Promise<Project> {
  const { data } = await api.post<Project>(`/projects/${id}/archive/`)
  return data
}

export async function restoreProject(
  id: string,
  status?: string,
): Promise<Project> {
  const { data } = await api.post<Project>(`/projects/${id}/restore/`, {
    ...(status ? { status } : {}),
  })
  return data
}

export async function deleteProject(id: string): Promise<void> {
  await api.delete(`/projects/${id}/`)
}

export async function fetchProjectMembers(id: string): Promise<ProjectMember[]> {
  const { data } = await api.get<ProjectMember[]>(`/projects/${id}/members/`)
  return data
}

export async function addProjectMember(
  id: string,
  userId: string,
): Promise<ProjectMember> {
  const { data } = await api.post<ProjectMember>(
    `/projects/${id}/members/`,
    { user: userId },
  )
  return data
}

export async function removeProjectMember(
  id: string,
  memberId: string,
): Promise<void> {
  await api.delete(`/projects/${id}/members/${memberId}/`)
}
