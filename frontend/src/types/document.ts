export type EntityKind = "COMPANY" | "PROJECT" | "CUSTOMER"

export interface Document {
  id: string
  original_filename: string
  mime_type: string
  size: number
  entity_kind: EntityKind
  entity_id: string | null
  uploaded_by: string
  uploaded_by_name: string
  url: string | null
  created_at: string
  updated_at: string
}
