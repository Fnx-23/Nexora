import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { Skeleton } from "@/components/ui/LoadingState"
import { useAuth } from "@/hooks/useAuth"

import { ActivityRow } from "./ActivityRow"
import { activityKeys, fetchActivities } from "./api"

export interface RecentActivityProps {
  limit?: number
  showViewAll?: boolean
  className?: string
}

export function RecentActivity({ limit = 6, showViewAll = true, className }: RecentActivityProps) {
  const { activeCompany } = useAuth()
  const companyId = activeCompany?.id ?? null

  const { data, isPending, isError, refetch } = useQuery({
    queryKey: activityKeys.recent(companyId, limit),
    queryFn: () => fetchActivities({ page_size: limit, ordering: "-timestamp" }),
    enabled: companyId !== null,
  })

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Recent Activity</CardTitle>
          {showViewAll && (
            <Link
              to="/activity"
              className="text-sm font-medium text-brand-600 hover:text-brand-700"
            >
              View all
            </Link>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isPending ? (
          <ul className="space-y-4">
            {Array.from({ length: Math.min(limit, 5) }, (_, i) => (
              <li key={i} className="flex items-start gap-3">
                <Skeleton className="size-7 shrink-0 rounded-full" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-40" />
                </div>
              </li>
            ))}
          </ul>
        ) : isError ? (
          <p className="text-sm text-surface-500">
            Couldn&apos;t load activity.{" "}
            <button
              type="button"
              onClick={() => void refetch()}
              className="font-medium text-brand-600 hover:text-brand-700"
            >
              Retry
            </button>
          </p>
        ) : !data || data.results.length === 0 ? (
          <p className="text-sm text-surface-500">No activity yet.</p>
        ) : (
          <ul className="space-y-4">
            {data.results.map((activity) => (
              <ActivityRow key={activity.id} activity={activity} />
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
