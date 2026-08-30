import { api } from "@/services/api"
import type { Paginated } from "@/types/api"
import type { Notification, UnreadCountResponse, MarkAllReadResponse } from "@/types/notification"

export async function fetchNotifications(params: {
  page?: number
  page_size?: number
  unread?: boolean
} = {}): Promise<Paginated<Notification>> {
  const query: Record<string, string | number> = {}
  if (params.page) query.page = params.page
  if (params.page_size) query.page_size = params.page_size
  if (params.unread) query.unread = "true"
  const { data } = await api.get<Paginated<Notification>>("/notifications/", { params: query })
  return data
}

export async function fetchUnreadCount(): Promise<UnreadCountResponse> {
  const { data } = await api.get<UnreadCountResponse>("/notifications/unread-count/")
  return data
}

export async function markNotificationRead(id: string): Promise<Notification> {
  const { data } = await api.patch<Notification>(`/notifications/${id}/mark-read/`)
  return data
}

export async function markAllNotificationsRead(): Promise<MarkAllReadResponse> {
  const { data } = await api.patch<MarkAllReadResponse>("/notifications/mark-all-read/")
  return data
}
