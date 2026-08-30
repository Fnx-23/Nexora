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

/**
 * React Query keys for the activity feature.
 *
 * Kept local to the feature (rather than in the shared `queryKeys` factory) so
 * the audit log stays self-contained and does not couple to unrelated features.
 * Every key is scoped by `companyId` so a tenant switch never serves cached
 * data from another company.
 */
export const activityKeys = {
  all: (companyId: string | null) => ["activities", companyId] as const,
  list: (companyId: string | null, params: ActivityListParams) =>
    ["activities", companyId, "list", params] as const,
  recent: (companyId: string | null, limit: number) =>
    ["activities", companyId, "recent", limit] as const,
}

/** Fetch a page of audit-log activities for the active company (read-only). */
export async function fetchActivities(
  params: ActivityListParams = {},
): Promise<Paginated<Activity>> {
  const { data } = await api.get<Paginated<Activity>>("/activities/", { params })
  return data
}
