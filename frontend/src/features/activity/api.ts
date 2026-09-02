import { api } from "@/services/api"
import type { Activity } from "@/types/activity"
import type { Paginated } from "@/types/api"

export interface ActivityListParams {
  page?: number
  page_size?: number
  action?: string
  entity_type?: string
  entity_id?: string
  actor?: string
  ordering?: string
}

export const activityKeys = {
  all: (companyId: string | null) => ["activities", companyId] as const,
  list: (companyId: string | null, params: ActivityListParams) =>
    ["activities", companyId, "list", params] as const,
  recent: (companyId: string | null, limit: number) =>
    ["activities", companyId, "recent", limit] as const,
}

export async function fetchActivities(
  params: ActivityListParams = {},
): Promise<Paginated<Activity>> {
  const { data } = await api.get<Paginated<Activity>>("/activities/", { params })
  return data
}
