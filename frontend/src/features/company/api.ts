import { api } from "@/services/api"

export interface Workspace {
  id: string
  name: string
  slug: string
  description: string
  is_active: boolean
  timezone: string
  locale: string
  logo: string | null
  created_at: string
  updated_at: string
}

export interface WorkspaceUpdate {
  name?: string
  description?: string
  timezone?: string
  locale?: string
  logo?: File
}

export async function fetchWorkspace(): Promise<Workspace> {
  const { data } = await api.get<Workspace>("/companies/current/")
  return data
}

export async function updateWorkspace(payload: WorkspaceUpdate): Promise<Workspace> {
  if (payload.logo) {
    const formData = new FormData()
    if (payload.name !== undefined) formData.append("name", payload.name)
    if (payload.description !== undefined) formData.append("description", payload.description)
    if (payload.timezone !== undefined) formData.append("timezone", payload.timezone)
    if (payload.locale !== undefined) formData.append("locale", payload.locale)
    formData.append("logo", payload.logo)
    const { data } = await api.patch<Workspace>("/companies/current/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    return data
  }
  const rest: Omit<WorkspaceUpdate, "logo"> = { ...payload }
  const { data } = await api.patch<Workspace>("/companies/current/", rest)
  return data
}