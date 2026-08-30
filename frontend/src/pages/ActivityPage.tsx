import { useCallback, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"

import { PageHeader } from "@/components/layout/PageHeader"
import { Button } from "@/components/ui/Button"
import { Card, CardContent } from "@/components/ui/Card"
import { EmptyState } from "@/components/ui/EmptyState"
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
            <EmptyState
              title="No activity found"
              description={
                hasFilters
                  ? "Try adjusting your filters."
                  : "Activity will appear here as your team creates and updates records."
              }
            />
          ) : (
            <>
              <Card>
                <CardContent className="pt-6">
                  <ul className="space-y-5">
                    {data.results.map((activity) => (
                      <ActivityRow key={activity.id} activity={activity} />
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {totalPages > 1 && (
                <Card>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-slate-500">
                        Page {page} of {totalPages}
                      </span>
                      <div className="flex gap-2">
                        <Button
                          variant="secondary"
                          size="sm"
                          disabled={page <= 1}
                          onClick={() => setPage((p) => p - 1)}
                        >
                          Previous
                        </Button>
                        <Button
                          variant="secondary"
                          size="sm"
                          disabled={page >= totalPages}
                          onClick={() => setPage((p) => p + 1)}
                        >
                          Next
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
