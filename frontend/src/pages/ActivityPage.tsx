import { useCallback, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"

import { PageHeader } from "@/components/layout/PageHeader"
import { ErrorState } from "@/components/ui/ErrorState"
import { LoadingState } from "@/components/ui/LoadingState"
import { Select } from "@/components/ui/Select"
import { ActivityRow } from "@/features/activity/ActivityRow"
import {
  activityKeys,
  fetchActivities,
  type ActivityListParams,
} from "@/features/activity/api"
import { ACTION_OPTIONS, ENTITY_TYPE_OPTIONS } from "@/features/activity/format"
import { useAuth } from "@/hooks/useAuth"

const PAGE_SIZE = 25

export function ActivityPage() {
  const { activeCompany } = useAuth()
  const companyId = activeCompany?.id ?? null

  const [actionFilter, setActionFilter] = useState("")
  const [entityFilter, setEntityFilter] = useState("")
  const [page, setPage] = useState(1)

  const queryParams = useMemo<ActivityListParams>(() => {
    const params: ActivityListParams = { page, page_size: PAGE_SIZE }
    if (actionFilter) params.action = actionFilter
    if (entityFilter) params.entity_type = entityFilter
    return params
  }, [page, actionFilter, entityFilter])

  const activitiesQuery = useQuery({
    queryKey: activityKeys.list(companyId, queryParams),
    queryFn: () => fetchActivities(queryParams),
    enabled: companyId !== null,
  })

  const handleActionChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setActionFilter(e.target.value)
    setPage(1)
  }, [])

  const handleEntityChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setEntityFilter(e.target.value)
    setPage(1)
  }, [])

  const data = activitiesQuery.data
  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1
  const hasFilters = Boolean(actionFilter || entityFilter)

  return (
    <div>
      <PageHeader
        title="Activity"
        description="A read-only audit log of important events across your workspace."
      />

      {activitiesQuery.isPending && <LoadingState label="Loading activity…" />}

      {activitiesQuery.isError && (
        <ErrorState
          title="Could not load activity"
          description="The server rejected or dropped the request. Check your connection and try again."
          onRetry={() => void activitiesQuery.refetch()}
        />
      )}

      {data && (
        <div className="space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <Select
              value={entityFilter}
              onChange={handleEntityChange}
              className="sm:max-w-[180px]"
              aria-label="Filter by type"
            >
              {ENTITY_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </Select>
            <Select
              value={actionFilter}
              onChange={handleActionChange}
              className="sm:max-w-[240px]"
              aria-label="Filter by action"
            >
              {ACTION_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </Select>
            {data.count > 0 && (
              <span className="ml-auto text-sm text-slate-500">
                {data.count} event{data.count !== 1 ? "s" : ""}
              </span>
            )}
          </div>

          {data.results.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-lg border border-slate-200 bg-white py-16 text-center">
              <p className="text-sm font-medium text-slate-500">
                {hasFilters ? "No activity found" : "No activity yet"}
              </p>
              <p className="mt-1 max-w-sm text-sm text-slate-400">
                {hasFilters
                  ? "Try adjusting your filters."
                  : "Activity will appear here as your team creates and updates records."}
              </p>
            </div>
          ) : (
            <>
              <div className="rounded-lg border border-slate-200 bg-white">
                <ul className="divide-y divide-slate-100">
                  {data.results.map((activity) => (
                    <li key={activity.id} className="px-5 py-3.5">
                      <ActivityRow activity={activity} />
                    </li>
                  ))}
                </ul>
              </div>

              {totalPages > 1 && (
                <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3">
                  <span className="text-sm text-slate-500">
                    Page {page} of {totalPages}
                  </span>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      disabled={page <= 1}
                      onClick={() => setPage((p) => p - 1)}
                      className="inline-flex items-center justify-center rounded-md border border-slate-200 bg-white px-3.5 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:pointer-events-none disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <button
                      type="button"
                      disabled={page >= totalPages}
                      onClick={() => setPage((p) => p + 1)}
                      className="inline-flex items-center justify-center rounded-md border border-slate-200 bg-white px-3.5 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:pointer-events-none disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
