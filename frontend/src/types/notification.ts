export interface Notification {
  id: string
  verb: string
  entity_type: string
  entity_id: string | null
  entity_name: string
  link: string
  is_read: boolean
  actor_name: string
  created_at: string
}

export interface UnreadCountResponse {
  count: number
}

export interface MarkAllReadResponse {
  updated: number
}
