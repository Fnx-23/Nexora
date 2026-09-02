import { useState } from "react"
import { Link } from "react-router-dom"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"
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
  TimelineChart,
} from "./ReportCharts"
import type { TimeReport } from "@/types/report"

export function TimeReportView({
  data,
}: {
  data: TimeReport
}) {
  const { summary, hours_by_project, hours_by_user, timeline, entries } = data
  const [subTab, setSubTab] = useState<"summary" | "detailed">("summary")

  const projectBars = hours_by_project.map((p) => ({
    id: p.project_id,
    label: p.project_name,
    sublabel: p.customer_name,
    value: p.hours,
    formattedValue: `${p.hours.toFixed(1)}h (${p.percentage}%)`,
    color: "bg-brand-500",
  }))

  const userBars = hours_by_user.map((u) => ({
    id: u.user_id,
    label: u.user_name,
    sublabel: u.email,
    value: u.hours,
    formattedValue: `${u.hours.toFixed(1)}h (${u.percentage}%)`,
    color: "bg-emerald-500",
  }))

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Total Logged Time
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.total_hours.toFixed(1)}h
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Across {summary.total_entries} entries
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Active Projects
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.active_projects_count}
            </p>
            <p className="mt-1 text-xs text-slate-500">Projects with time logged</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Active Contributors
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.active_users_count}
            </p>
            <p className="mt-1 text-xs text-slate-500">Team members logging time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Active Days
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.days_with_activity}
            </p>
            <p className="mt-1 text-xs text-slate-500">Days with recorded time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Avg. Daily Hours
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.avg_daily_hours.toFixed(1)}h
            </p>
            <p className="mt-1 text-xs text-slate-500">Per active day</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Daily Tracked Hours Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <TimelineChart
            items={timeline}
            emptyMessage="No time tracked across this date range."
          />
        </CardContent>
      </Card>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Time Allocation by Project</CardTitle>
          </CardHeader>
          <CardContent>
            <HorizontalBarChart
              items={projectBars}
              emptyMessage="No project time data in this range."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Time Allocation by Contributor</CardTitle>
          </CardHeader>
          <CardContent>
            <HorizontalBarChart
              items={userBars}
              emptyMessage="No contributor time data in this range."
            />
          </CardContent>
        </Card>
      </div>

      <div className="flex border-b border-slate-200">
        <button
          type="button"
          onClick={() => setSubTab("summary")}
          className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
            subTab === "summary"
              ? "border-brand-600 text-brand-600"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Hours Breakdown Tables
        </button>
        <button
          type="button"
          onClick={() => setSubTab("detailed")}
          className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
            subTab === "detailed"
              ? "border-brand-600 text-brand-600"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Detailed Time Entries Log ({entries.length})
        </button>
      </div>

      {subTab === "summary" ? (
        <div className="grid gap-5 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Project Hours</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {hours_by_project.length === 0 ? (
                <EmptyState title="No project time" description="No hours logged." />
              ) : (
                <TableContainer>
                  <Table>
                    <THead>
                      <TR>
                        <TH>Project</TH>
                        <TH>Hours</TH>
                        <TH>% Share</TH>
                        <TH>Entries</TH>
                      </TR>
                    </THead>
                    <TBody>
                      {hours_by_project.map((p) => (
                        <TR key={p.project_id}>
                          <TD>
                            <Link
                              to={`/projects/${p.project_id}`}
                              className="font-medium text-slate-900 hover:text-brand-600"
                            >
                              {p.project_name}
                            </Link>
                            <p className="text-xs text-slate-500">{p.customer_name}</p>
                          </TD>
                          <TD className="tabular-nums font-semibold text-slate-900">
                            {p.hours.toFixed(1)}h
                          </TD>
                          <TD className="min-w-[100px]">
                            <ProgressBar value={p.percentage} />
                          </TD>
                          <TD className="tabular-nums text-slate-600">
                            {p.entry_count}
                          </TD>
                        </TR>
                      ))}
                    </TBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Contributor Hours</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              {hours_by_user.length === 0 ? (
                <EmptyState title="No contributor time" description="No hours logged." />
              ) : (
                <TableContainer>
                  <Table>
                    <THead>
                      <TR>
                        <TH>Contributor</TH>
                        <TH>Hours</TH>
                        <TH>% Share</TH>
                        <TH>Entries</TH>
                      </TR>
                    </THead>
                    <TBody>
                      {hours_by_user.map((u) => (
                        <TR key={u.user_id}>
                          <TD>
                            <p className="font-medium text-slate-900">{u.user_name}</p>
                            <p className="text-xs text-slate-500">{u.email}</p>
                          </TD>
                          <TD className="tabular-nums font-semibold text-slate-900">
                            {u.hours.toFixed(1)}h
                          </TD>
                          <TD className="min-w-[100px]">
                            <ProgressBar value={u.percentage} />
                          </TD>
                          <TD className="tabular-nums text-slate-600">
                            {u.entry_count}
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
      ) : (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle>Detailed Time Log Entries</CardTitle>
            <span className="text-xs text-slate-500">
              Showing latest {entries.length} entries
            </span>
          </CardHeader>
          <CardContent className="pt-0">
            {entries.length === 0 ? (
              <EmptyState
                title="No time entries"
                description="Try adjusting your date range or filters."
              />
            ) : (
              <TableContainer>
                <Table>
                  <THead>
                    <TR>
                      <TH>Date</TH>
                      <TH>Project</TH>
                      <TH>Contributor</TH>
                      <TH className="hidden sm:table-cell">Task</TH>
                      <TH>Duration</TH>
                      <TH className="hidden md:table-cell">Time Window</TH>
                      <TH className="hidden lg:table-cell">Description</TH>
                    </TR>
                  </THead>
                  <TBody>
                    {entries.map((e) => (
                      <TR key={e.id}>
                        <TD className="text-sm font-medium text-slate-900">
                          {e.date}
                        </TD>
                        <TD>
                          <Link
                            to={`/projects/${e.project_id}`}
                            className="font-medium text-slate-900 hover:text-brand-600"
                          >
                            {e.project_name}
                          </Link>
                        </TD>
                        <TD className="text-slate-700">{e.user_name}</TD>
                        <TD className="hidden sm:table-cell text-slate-500 text-xs">
                          {e.task_title || "—"}
                        </TD>
                        <TD className="tabular-nums font-semibold text-slate-900">
                          {e.duration_hours.toFixed(2)}h
                        </TD>
                        <TD className="hidden md:table-cell text-xs text-slate-500">
                          {e.start_time ? e.start_time.slice(0, 5) : "—"}
                          {e.end_time ? ` - ${e.end_time.slice(0, 5)}` : ""}
                        </TD>
                        <TD className="hidden lg:table-cell max-w-[200px] truncate text-xs text-slate-600">
                          {e.description || "—"}
                        </TD>
                      </TR>
                    ))}
                  </TBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
