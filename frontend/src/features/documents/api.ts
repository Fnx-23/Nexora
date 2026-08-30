import { api } from "@/services/api"
import type { Paginated } from "@/types/api"
import type { Document, EntityKind } from "@/types/document"

export async function fetchDocuments(params: {
  entity_kind?: EntityKind
  entity_id?: string
  page?: number
  page_size?: number
} = {}): Promise<Paginated<Document>> {
  const query: Record<string, string | number> = {}
  if (params.entity_kind) query.entity_kind = params.entity_kind
  if (params.entity_id) query.entity_id = params.entity_id
  if (params.page) query.page = params.page
  if (params.page_size) query.page_size = params.page_size
  const { data } = await api.get<Paginated<Document>>("/documents/", { params: query })
  return data
}

export async function uploadDocument(
  file: File,
  entityKind: EntityKind,
  entityId: string,
): Promise<Document> {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("entity_kind", entityKind)
  formData.append("entity_id", entityId)
  const { data } = await api.post<Document>("/documents/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  })
  return data
}

export async function downloadDocumentUrl(id: string): Promise<string> {
  const { data } = await api.get<{ url: string }>(`/documents/${id}/download/`)
  return data.url
}

export async function renameDocument(id: string, filename: string): Promise<Document> {
  const { data } = await api.patch<Document>(`/documents/${id}/rename/`, { filename })
  return data
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/documents/${id}/`)
}
