import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
import { StatusBadge } from "@/components/ui/Badge"
import { Avatar } from "@/components/ui/Avatar"
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
  HorizontalBarChart,
  ProgressBar,
  WorkloadStackedBar,
} from "./ReportCharts"
import type { TeamWorkloadReport } from "@/types/report"

export function TeamWorkloadReportView({
  data,
}: {
  data: TeamWorkloadReport
}) {
  const { summary, results } = data

  const openTasksBars = results.map((m) => ({
    id: m.user_id,
    label: m.name,
    sublabel: m.role,
    value: m.open_tasks,
    formattedValue: `${m.open_tasks} open (${m.assigned_tasks} total)`,
    color: m.open_tasks > 5 ? "bg-amber-500" : "bg-sky-500",
  }))

  const hoursBars = results.map((m) => ({
    id: m.user_id,
    label: m.name,
    sublabel: m.role,
    value: m.tracked_hours,
    formattedValue: `${m.tracked_hours.toFixed(1)}h`,
    color: "bg-emerald-500",
  }))

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Active Members
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.total_members}
            </p>
            <p className="mt-1 text-xs text-slate-500">In company workspace</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Assigned Tasks
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.total_assigned_tasks}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {summary.total_open_tasks} open across team
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Completion Rate
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.overall_completion_rate}%
            </p>
            <ProgressBar
              value={summary.overall_completion_rate}
              showLabel={false}
              className="mt-2"
            />
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
              {summary.total_overdue_tasks > 0 ? "Assigned tasks past deadline" : "No overdue tasks"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Team Hours Logged
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.total_tracked_hours.toFixed(1)}h
            </p>
            <p className="mt-1 text-xs text-slate-500">Total logged time</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Active Open Tasks by Member</CardTitle>
          </CardHeader>
          <CardContent>
            <HorizontalBarChart
              items={openTasksBars}
              emptyMessage="No open tasks assigned."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Tracked Hours by Team Member</CardTitle>
          </CardHeader>
          <CardContent>
            <HorizontalBarChart
              items={hoursBars}
              emptyMessage="No hours logged by team members in this period."
            />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle>Team Member Workload Breakdown</CardTitle>
          <span className="text-xs text-slate-500">
            {results.length} member{results.length !== 1 ? "s" : ""}
          </span>
        </CardHeader>
        <CardContent className="pt-0">
          {results.length === 0 ? (
            <EmptyState
              title="No team members found"
              description="Adjust your filters to view workload."
            />
          ) : (
            <TableContainer>
              <Table>
                <THead>
                  <TR>
                    <TH>Team Member</TH>
                    <TH>Role</TH>
                    <TH>Assigned</TH>
                    <TH>Open</TH>
                    <TH>Done</TH>
                    <TH>Overdue</TH>
                    <TH className="min-w-[150px]">Task Distribution</TH>
                    <TH>Tracked Hours</TH>
                    <TH className="min-w-[120px]">Completion</TH>
                  </TR>
                </THead>
                <TBody>
                  {results.map((m) => (
                    <TR key={m.user_id}>
                      <TD>
                        <div className="flex items-center gap-3">
                          <Avatar name={m.name} size="sm" />
                          <div>
                            <p className="font-medium text-slate-900">{m.name}</p>
                            <p className="text-xs text-slate-500">{m.email}</p>
                          </div>
                        </div>
                      </TD>
                      <TD>
                        <StatusBadge value={m.role} />
                      </TD>
                      <TD className="tabular-nums font-semibold text-slate-900">
                        {m.assigned_tasks}
                      </TD>
                      <TD className="tabular-nums font-medium text-sky-600">
                        {m.open_tasks}
                      </TD>
                      <TD className="tabular-nums font-medium text-emerald-600">
                        {m.completed_tasks}
                      </TD>
                      <TD>
                        {m.overdue_tasks > 0 ? (
                          <span className="inline-flex items-center rounded-full bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-700">
                            {m.overdue_tasks}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">0</span>
                        )}
                      </TD>
                      <TD>
                        <WorkloadStackedBar
                          completed={m.completed_tasks}
                          open={m.open_tasks}
                          overdue={m.overdue_tasks}
                        />
                      </TD>
                      <TD className="tabular-nums font-semibold text-slate-900">
                        {m.tracked_hours.toFixed(1)}h
                      </TD>
                      <TD>
                        <ProgressBar value={m.completion_rate} />
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
