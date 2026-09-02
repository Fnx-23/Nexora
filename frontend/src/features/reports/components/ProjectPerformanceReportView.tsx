import { Link } from "react-router-dom"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { StatusBadge } from "@/components/ui/Badge"
import { EmptyState } from "@/components/ui/EmptyState"
import {
  Table,
  TableContainer,
  TBody,
  TD,
  TH,
  THead,
  TR,
} from "@/components/ui/Table"
import {
  DistributionBar,
  HorizontalBarChart,
  ProgressBar,
} from "./ReportCharts"
import type { ProjectPerformanceReport } from "@/types/report"

const STATUS_COLORS: Record<string, string> = {
  PLANNING: "bg-sky-500",
  IN_PROGRESS: "bg-amber-500",
  ON_HOLD: "bg-orange-400",
  COMPLETED: "bg-emerald-500",
  ARCHIVED: "bg-slate-400",
}

export function ProjectPerformanceReportView({
  data,
}: {
  data: ProjectPerformanceReport
}) {
  const { summary, status_distribution, results } = data

  const statusSegments = status_distribution.map((s) => ({
    key: s.status,
    label: s.label,
    value: s.count,
    percentage:
      summary.total_projects > 0
        ? Math.round((s.count / summary.total_projects) * 100)
        : 0,
    colorClass: STATUS_COLORS[s.status] || "bg-slate-400",
  }))

  const effortBars = results.map((p) => ({
    id: p.project_id,
    label: p.project_name,
    sublabel: p.customer_name || undefined,
    value: p.tracked_hours,
    formattedValue: `${p.tracked_hours.toFixed(1)}h`,
    color: "bg-brand-500",
  }))

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Total Projects
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.total_projects}
            </p>
            <p className="mt-1 text-xs text-slate-500">In current filter</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Tracked Hours
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.total_tracked_hours.toFixed(1)}h
            </p>
            <p className="mt-1 text-xs text-slate-500">Total logged time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Avg. Progress
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.average_progress}%
            </p>
            <ProgressBar value={summary.average_progress} showLabel={false} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Tasks (Done / Open)
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.total_completed_tasks} / {summary.total_open_tasks}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {summary.total_tasks} total tasks
            </p>
          </CardContent>
        </Card>

        <Card className={summary.total_overdue_tasks > 0 ? "border-rose-200 bg-rose-50/20" : ""}>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Overdue Tasks
            </p>
          </CardHeader>
          <CardContent>
            <p
              className={`text-2xl font-bold tabular-nums ${
                summary.total_overdue_tasks > 0 ? "text-rose-600" : "text-slate-900"
              }`}
            >
              {summary.total_overdue_tasks}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {summary.total_overdue_tasks > 0 ? "Needs immediate attention" : "All on schedule"}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Project Status Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <DistributionBar
              segments={statusSegments}
              emptyMessage="No projects available in selected range."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Effort Invested by Project (Hours)</CardTitle>
          </CardHeader>
          <CardContent>
            <HorizontalBarChart
              items={effortBars}
              emptyMessage="No time tracked for matching projects."
            />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle>Project Performance Breakdown</CardTitle>
          <span className="text-xs text-slate-500">
            {results.length} project{results.length !== 1 ? "s" : ""}
          </span>
        </CardHeader>
        <CardContent className="pt-0">
          {results.length === 0 ? (
            <EmptyState
              title="No projects found"
              description="Try adjusting your date range or filters."
            />
          ) : (
            <TableContainer>
              <Table>
                <THead>
                  <TR>
                    <TH>Project</TH>
                    <TH>Customer</TH>
                    <TH>Status</TH>
                    <TH className="min-w-[140px]">Progress</TH>
                    <TH>Completed</TH>
                    <TH>Open</TH>
                    <TH>Overdue</TH>
                    <TH>Tracked Hours</TH>
                    <TH className="hidden sm:table-cell">Deadline</TH>
                  </TR>
                </THead>
                <TBody>
                  {results.map((p) => (
                    <TR key={p.project_id}>
                      <TD>
                        <Link
                          to={`/projects/${p.project_id}`}
                          className="font-medium text-slate-900 hover:text-brand-600 transition-colors"
                        >
                          {p.project_name}
                        </Link>
                        {p.manager_name && (
                          <p className="text-[11px] text-slate-600">Lead: {p.manager_name}</p>
                        )}
                      </TD>
                      <TD className="text-slate-600">
                        {p.customer_name || <span className="text-slate-600">—</span>}
                      </TD>
                      <TD>
                        <StatusBadge value={p.status} />
                      </TD>
                      <TD>
                        <ProgressBar value={p.progress} />
                      </TD>
                      <TD className="tabular-nums font-medium text-emerald-600">
                        {p.completed_tasks}
                      </TD>
                      <TD className="tabular-nums font-medium text-sky-600">
                        {p.open_tasks}
                      </TD>
                      <TD>
                        {p.overdue_tasks > 0 ? (
                          <span className="inline-flex items-center rounded-full bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-700">
                            {p.overdue_tasks} overdue
                          </span>
                        ) : (
                          <span className="text-xs text-slate-600">0</span>
                        )}
                      </TD>
                      <TD className="tabular-nums font-semibold text-slate-900">
                        {p.tracked_hours.toFixed(1)}h
                      </TD>
                      <TD className="hidden sm:table-cell text-xs text-slate-600">
                        {p.deadline || "—"}
                      </TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
