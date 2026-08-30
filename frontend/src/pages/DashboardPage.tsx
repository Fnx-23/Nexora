import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"

import { PageHeader } from "@/components/layout/PageHeader"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { StatusBadge } from "@/components/ui/Badge"
import { Skeleton } from "@/components/ui/LoadingState"
import { ErrorState } from "@/components/ui/ErrorState"
import { EmptyState } from "@/components/ui/EmptyState"
import { useAuth } from "@/hooks/useAuth"
import { fetchDashboard } from "@/features/dashboard/api"
import { queryKeys } from "@/utils/queryKeys"
import { cn } from "@/utils/cn"

export function DashboardPage() {
  const { user, activeCompany, role } = useAuth()

  const companyId = activeCompany?.id ?? null

  const {
    data: dashboard,
    isLoading,
    error,
  } = useQuery({
    queryKey: queryKeys.dashboard(companyId),
    queryFn: fetchDashboard,
    enabled: !!companyId,
  })

  const firstName = user?.first_name || user?.email.split("@")[0] || "there"

  if (error) {
    return (
      <div>
        <PageHeader
          title={`Welcome back, ${firstName}`}
          description={
            activeCompany
              ? `You are working in ${activeCompany.name}.`
              : "Your account is not linked to a company yet."
          }
        />
        <ErrorState description="Failed to load dashboard data. Please try again." />
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title={`Welcome back, ${firstName}`}
        description={
          activeCompany
            ? `You are working in ${activeCompany.name}.`
            : "Your account is not linked to a company yet."
        }
      />

      {/* KPI Cards */}
      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-4">
        {isLoading ? (
          <KpiCardSkeleton count={4} />
        ) : (
          <>
            <KpiCard
              label="Active Projects"
              value={dashboard?.kpis.active_projects ?? 0}
              hint={`${dashboard?.kpis.total_projects ?? 0} total`}
            />
            <KpiCard
              label="Open Tasks"
              value={dashboard?.kpis.open_tasks ?? 0}
              hint={
                (dashboard?.kpis.overdue_tasks ?? 0) > 0
                  ? `${dashboard?.kpis.overdue_tasks} overdue`
                  : "No overdue"
              }
              danger={(dashboard?.kpis.overdue_tasks ?? 0) > 0}
            />
            <KpiCard
              label="Customers"
              value={dashboard?.kpis.total_customers ?? 0}
              hint="All time"
            />
            <KpiCard
              label="Team Members"
              value={dashboard?.kpis.team_members ?? 0}
              hint={`${dashboard?.kpis.completed_tasks ?? 0} tasks completed`}
            />
          </>
        )}
      </div>

      {/* Status distributions + Activity */}
      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <StatusDistSkeleton />
            ) : !dashboard ? (
              <EmptyState title="No data available." />
            ) : (
              <div className="space-y-8">
                <StatusBars
                  title="Projects"
                  items={dashboard.project_status_distribution}
                  linkTo="/projects"
                />
                <StatusBars
                  title="Tasks"
                  items={dashboard.task_status_distribution}
                  linkTo="/tasks"
                />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Your access sidebar */}
        <Card>
          <CardHeader>
            <CardTitle>Your Access</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="space-y-4 text-sm">
              <div>
                <dt className="text-slate-500">Company</dt>
                <dd className="font-medium text-slate-900">{activeCompany?.name ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Workspace</dt>
                <dd className="font-medium text-slate-900">{activeCompany?.slug ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Role</dt>
                <dd className="font-medium text-slate-900">{role ? titleCase(role) : "—"}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>

      {/* Recent items + Activity feed */}
      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        {/* Recent Projects */}
        <Card className="min-w-0">
          <CardHeader>
            <CardTitle>Recent Projects</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <RecentSkeleton count={5} />
            ) : !dashboard?.recent_projects.length ? (
              <p className="text-sm text-slate-500">No projects yet.</p>
            ) : (
              <ul className="space-y-3">
                {dashboard.recent_projects.map((p) => (
                  <li key={p.id}>
                    <Link
                      to={`/projects/${p.id}`}
                      className="flex items-center justify-between rounded-lg px-2 py-1.5 transition-colors hover:bg-slate-50"
                    >
                      <span className="truncate text-sm font-medium text-slate-900">
                        {p.name}
                      </span>
                      <StatusBadge value={p.status} />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Recent Tasks */}
        <Card className="min-w-0">
          <CardHeader>
            <CardTitle>Recent Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <RecentSkeleton count={5} />
            ) : !dashboard?.recent_tasks.length ? (
              <p className="text-sm text-slate-500">No tasks yet.</p>
            ) : (
              <ul className="space-y-3">
                {dashboard.recent_tasks.map((t) => (
                  <li key={t.id}>
                    <Link
                      to="/tasks"
                      className="flex items-center justify-between rounded-lg px-2 py-1.5 transition-colors hover:bg-slate-50"
                    >
                      <span className="truncate text-sm font-medium text-slate-900">{t.title}</span>
                      <StatusBadge value={t.status} />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Activity Feed */}
        <Card className="min-w-0">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <RecentSkeleton count={5} />
            ) : !dashboard?.activity.length ? (
              <p className="text-sm text-slate-500">No activity yet.</p>
            ) : (
              <ul className="space-y-3">
                {dashboard.activity.map((item, idx) => (
                  <li key={`${item.type}-${item.id}-${idx}`} className="flex items-center gap-3">
                    <span
                      className={cn(
                        "flex size-7 shrink-0 items-center justify-center rounded-full text-xs font-medium",
                        item.type === "project"
                          ? "bg-brand-50 text-brand-700"
                          : "bg-emerald-50 text-emerald-700",
                      )}
                    >
                      {item.type === "project" ? "P" : "T"}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm text-slate-900">{item.name}</p>
                      <p className="text-xs text-slate-500">
                        {timeAgo(item.updated_at)}
                      </p>
                    </div>
                    <StatusBadge value={item.status} />
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/* Sub-components                                                             */
/* -------------------------------------------------------------------------- */

function KpiCard({
  label,
  value,
  hint,
  danger = false,
}: {
  label: string
  value: number
  hint: string
  danger?: boolean
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <p className="text-sm text-slate-500">{label}</p>
        <p className={cn("text-4xl leading-tight font-semibold tracking-tight", danger ? "text-red-600" : "text-slate-900")}>
          {value}
        </p>
      </CardHeader>
      <CardContent>
        <p className={cn("text-xs", danger ? "text-red-500" : "text-slate-400")}>{hint}</p>
      </CardContent>
    </Card>
  )
}

function KpiCardSkeleton({ count }: { count: number }) {
  return (
    <>
      {Array.from({ length: count }, (_, i) => (
        <Card key={i}>
          <CardHeader className="pb-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-16 mt-1" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-3 w-32" />
          </CardContent>
        </Card>
      ))}
    </>
  )
}

function StatusBars({
  title,
  items,
  linkTo,
}: {
  title: string
  items: { status: string; label: string; count: number }[]
  linkTo: string
}) {
  const total = items.reduce((sum, i) => sum + i.count, 0)
  if (total === 0) {
    return (
      <div>
        <p className="text-sm font-medium text-slate-700 mb-2">{title}</p>
        <p className="text-sm text-slate-500">No data.</p>
      </div>
    )
  }
  return (
    <div>
      <p className="text-sm font-medium text-slate-700 mb-2">{title}</p>
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-slate-100">
        {items.map((item) =>
          item.count > 0 ? (
            <Link
              key={item.status}
              to={linkTo}
              className={cn("h-full transition-opacity hover:opacity-80", STATUS_COLORS[item.status])}
              style={{ width: `${(item.count / total) * 100}%` }}
              title={`${item.label}: ${item.count}`}
            />
          ) : null,
        )}
      </div>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
        {items.map((item) => (
          <span key={item.status} className="flex items-center gap-1.5 text-xs text-slate-600">
            <span className={cn("inline-block size-2.5 rounded-full", STATUS_COLORS[item.status])} />
            {item.label}: {item.count}
          </span>
        ))}
      </div>
    </div>
  )
}

function StatusDistSkeleton() {
  return (
    <div className="space-y-8">
      {Array.from({ length: 2 }, (_, section) => (
        <div key={section}>
          <Skeleton className="h-4 w-16 mb-3" />
          <Skeleton className="h-3 w-full rounded-full" />
          <div className="mt-2 flex gap-4">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-20" />
          </div>
        </div>
      ))}
    </div>
  )
}

function RecentSkeleton({ count }: { count: number }) {
  return (
    <ul className="space-y-3">
      {Array.from({ length: count }, (_, i) => (
        <li key={i} className="flex items-center justify-between">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-5 w-16 rounded-full" />
        </li>
      ))}
    </ul>
  )
}

/* -------------------------------------------------------------------------- */
/* Helpers                                                                    */
/* -------------------------------------------------------------------------- */

const STATUS_COLORS: Record<string, string> = {
  PLANNING: "bg-sky-400",
  IN_PROGRESS: "bg-amber-400",
  ON_HOLD: "bg-orange-400",
  COMPLETED: "bg-emerald-400",
  ARCHIVED: "bg-slate-300",
  TODO: "bg-slate-400",
  IN_REVIEW: "bg-sky-400",
  DONE: "bg-emerald-400",
  CANCELLED: "bg-red-300",
}

function titleCase(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase()
}

function timeAgo(isoDate: string): string {
  const now = Date.now()
  const then = new Date(isoDate).getTime()
  const diffMs = now - then
  const diffMin = Math.floor(diffMs / 60_000)
  if (diffMin < 1) return "Just now"
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.floor(diffHr / 24)
  if (diffDay < 30) return `${diffDay}d ago`
  const diffMonth = Math.floor(diffDay / 30)
  return `${diffMonth}mo ago`
}
