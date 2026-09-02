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
import { HorizontalBarChart } from "./ReportCharts"
import type { CustomerOverviewReport } from "@/types/report"

export function CustomerOverviewReportView({
  data,
}: {
  data: CustomerOverviewReport
}) {
  const { summary, results } = data

  const customerHoursBars = results.map((c) => ({
    id: c.customer_id,
    label: c.display_name,
    sublabel: c.company_name ? c.customer_name : undefined,
    value: c.hours_tracked,
    formattedValue: `${c.hours_tracked.toFixed(1)}h`,
    color: "bg-brand-500",
  }))

  const customerProjectsBars = results.map((c) => ({
    id: c.customer_id,
    label: c.display_name,
    value: c.active_projects,
    formattedValue: `${c.active_projects} active / ${c.completed_projects} done`,
    color: c.active_projects > 0 ? "bg-emerald-500" : "bg-slate-300",
  }))

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Total Customers
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.total_customers}
            </p>
            <p className="mt-1 text-xs text-slate-500">In company account</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Active Engagements
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.active_customers}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              With ongoing projects
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
              {summary.total_active_projects}
            </p>
            <p className="mt-1 text-xs text-slate-500">Across all customers</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Completed Projects
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.total_completed_projects}
            </p>
            <p className="mt-1 text-xs text-slate-500">Delivered successfully</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-1">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Customer Tracked Time
            </p>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold tabular-nums text-slate-900">
              {summary.total_tracked_hours.toFixed(1)}h
            </p>
            <p className="mt-1 text-xs text-slate-500">Billed / tracked hours</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Delivery Hours by Customer</CardTitle>
          </CardHeader>
          <CardContent>
            <HorizontalBarChart
              items={customerHoursBars}
              emptyMessage="No time tracked for customers."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Active Client Engagements</CardTitle>
          </CardHeader>
          <CardContent>
            <HorizontalBarChart
              items={customerProjectsBars}
              emptyMessage="No active customer projects."
            />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle>Customer Portfolio Overview</CardTitle>
          <span className="text-xs text-slate-500">
            {results.length} customer{results.length !== 1 ? "s" : ""}
          </span>
        </CardHeader>
        <CardContent className="pt-0">
          {results.length === 0 ? (
            <EmptyState
              title="No customers found"
              description="Adjust your filters to view customer data."
            />
          ) : (
            <TableContainer>
              <Table>
                <THead>
                  <TR>
                    <TH>Customer</TH>
                    <TH>Status</TH>
                    <TH>Active Projects</TH>
                    <TH>Completed Projects</TH>
                    <TH>Total Projects</TH>
                    <TH>Open Tasks</TH>
                    <TH>Tracked Hours</TH>
                  </TR>
                </THead>
                <TBody>
                  {results.map((c) => (
                    <TR key={c.customer_id}>
                      <TD>
                        <Link
                          to="/customers"
                          className="font-medium text-slate-900 hover:text-brand-600 transition-colors"
                        >
                          {c.display_name}
                        </Link>
                        {c.company_name && c.customer_name && (
                          <p className="text-[11px] text-slate-500">Contact: {c.customer_name}</p>
                        )}
                        {c.email && (
                          <p className="text-[11px] text-slate-400">{c.email}</p>
                        )}
                      </TD>
                      <TD>
                        <StatusBadge value={c.status} />
                      </TD>
                      <TD className="tabular-nums font-semibold text-emerald-600">
                        {c.active_projects}
                      </TD>
                      <TD className="tabular-nums font-medium text-slate-700">
                        {c.completed_projects}
                      </TD>
                      <TD className="tabular-nums font-medium text-slate-900">
                        {c.total_projects}
                      </TD>
                      <TD className="tabular-nums text-sky-600">
                        {c.open_tasks}
                      </TD>
                      <TD className="tabular-nums font-semibold text-slate-900">
                        {c.hours_tracked.toFixed(1)}h
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
