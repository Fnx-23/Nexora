import { useCallback, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useSearchParams } from "react-router-dom"

import { PageHeader } from "@/components/layout/PageHeader"
import { ErrorState } from "@/components/ui/ErrorState"
import { LoadingState } from "@/components/ui/LoadingState"
import { CustomerOverviewReportView } from "@/features/reports/components/CustomerOverviewReportView"
import { ProjectPerformanceReportView } from "@/features/reports/components/ProjectPerformanceReportView"
import { ReportFilters } from "@/features/reports/components/ReportFilters"
import { TeamWorkloadReportView } from "@/features/reports/components/TeamWorkloadReportView"
import { TimeReportView } from "@/features/reports/components/TimeReportView"
import {
  downloadReportCsv,
  fetchCustomerOverviewReport,
  fetchProjectPerformanceReport,
  fetchTeamWorkloadReport,
  fetchTimeReport,
} from "@/features/reports/api"
import { fetchProjects } from "@/features/projects/api"
import { fetchMembers } from "@/features/team/api"
import { fetchCustomers } from "@/features/customers/api"
import { useAuth } from "@/hooks/useAuth"
import { queryKeys } from "@/utils/queryKeys"
import type { ReportFilterParams, ReportType } from "@/types/report"

const TABS: { id: ReportType; label: string; description: string }[] = [
  {
    id: "project-performance",
    label: "Project Performance",
    description: "Status, progress, completed/open tasks, overdue items, and tracked hours per project.",
  },
  {
    id: "team-workload",
    label: "Team Workload",
    description: "Assigned tasks, open workload, completed tasks, overdue items, and logged hours per member.",
  },
  {
    id: "time",
    label: "Time Report",
    description: "Tracked hours breakdown by project, by team member, daily timeline, and detailed logs.",
  },
  {
    id: "customer-overview",
    label: "Customer Overview",
    description: "Customer accounts, active vs completed project delivery, open tasks, and hours tracked.",
  },
]

export function ReportsPage() {
  const { activeCompany } = useAuth()
  const companyId = activeCompany?.id ?? null

  const [searchParams, setSearchParams] = useSearchParams()
  const tabParam = searchParams.get("tab") as ReportType | null
  const activeTab: ReportType =
    tabParam && TABS.some((t) => t.id === tabParam) ? tabParam : "project-performance"

  const [filters, setFilters] = useState<ReportFilterParams>({
    date_from: "",
    date_to: "",
    project: "",
    user: "",
    customer: "",
    status: "",
  })

  const [isExporting, setIsExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  const handleTabChange = useCallback(
    (newTab: ReportType) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev)
        next.set("tab", newTab)
        return next
      })
      setFilters((prev) => ({ ...prev, status: "" }))
    },
    [setSearchParams],
  )

  const handleFilterChange = useCallback((updates: Partial<ReportFilterParams>) => {
    setFilters((prev) => ({ ...prev, ...updates }))
  }, [])

  const handleResetFilters = useCallback(() => {
    setFilters({
      date_from: "",
      date_to: "",
      project: "",
      user: "",
      customer: "",
      status: "",
    })
  }, [])

  const projectsQuery = useQuery({
    queryKey: queryKeys.projects(companyId),
    queryFn: () => fetchProjects({ page_size: 100 }),
    enabled: !!companyId,
  })

  const membersQuery = useQuery({
    queryKey: queryKeys.members(companyId),
    queryFn: fetchMembers,
    enabled: !!companyId,
  })

  const customersQuery = useQuery({
    queryKey: queryKeys.customers(companyId),
    queryFn: () => fetchCustomers({ page_size: 100 }),
    enabled: !!companyId,
  })

  const projectOptions = useMemo(
    () => (projectsQuery.data?.results ?? []).map((p) => ({ id: p.id, name: p.name })),
    [projectsQuery.data],
  )

  const memberOptions = useMemo(
    () =>
      (membersQuery.data ?? []).map((m) => ({
        id: m.id,
        name: m.full_name || m.email,
      })),
    [membersQuery.data],
  )

  const customerOptions = useMemo(
    () =>
      (customersQuery.data?.results ?? []).map((c) => ({
        id: c.id,
        name: c.company_name || c.name,
      })),
    [customersQuery.data],
  )

  const projectPerfQuery = useQuery({
    queryKey: queryKeys.reports.projectPerformance(companyId, filters),
    queryFn: () => fetchProjectPerformanceReport(filters),
    enabled: !!companyId && activeTab === "project-performance",
  })

  const teamWorkloadQuery = useQuery({
    queryKey: queryKeys.reports.teamWorkload(companyId, filters),
    queryFn: () => fetchTeamWorkloadReport(filters),
    enabled: !!companyId && activeTab === "team-workload",
  })

  const timeReportQuery = useQuery({
    queryKey: queryKeys.reports.time(companyId, filters),
    queryFn: () => fetchTimeReport(filters),
    enabled: !!companyId && activeTab === "time",
  })

  const customerOverviewQuery = useQuery({
    queryKey: queryKeys.reports.customerOverview(companyId, filters),
    queryFn: () => fetchCustomerOverviewReport(filters),
    enabled: !!companyId && activeTab === "customer-overview",
  })

  const handleExportCsv = useCallback(async () => {
    try {
      setIsExporting(true)
      setExportError(null)
      await downloadReportCsv(activeTab, filters)
    } catch {
      setExportError("Failed to generate CSV export. Please try again.")
    } finally {
      setIsExporting(false)
    }
  }, [activeTab, filters])

  const activeTabMeta = TABS.find((t) => t.id === activeTab) || TABS[0]

  return (
    <div className="space-y-6">
      <div className="hidden print:block mb-6 border-b border-slate-300 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Nexora Business Report</h1>
            <p className="text-sm font-semibold text-brand-700">{activeCompany?.name}</p>
          </div>
          <div className="text-right text-xs text-slate-500">
            <p>Generated: {new Date().toLocaleDateString("en", { dateStyle: "long" })}</p>
            <p>Report: {activeTabMeta.label}</p>
          </div>
        </div>
        <p className="mt-2 text-xs text-slate-600">
          Filters:{" "}
          {[
            filters.date_from ? `From ${filters.date_from}` : null,
            filters.date_to ? `To ${filters.date_to}` : null,
            filters.status ? `Status: ${filters.status}` : null,
          ]
            .filter(Boolean)
            .join(" · ") || "All time, unconstrained"}
        </p>
      </div>

      <div className="print:hidden">
        <PageHeader
          title="Business Reports & Analytics"
          description={activeTabMeta.description}
        />

        <nav
          aria-label="Report tabs"
          className="mt-6 flex flex-wrap gap-2 border-b border-slate-200 pb-px"
        >
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => handleTabChange(tab.id)}
              className={`rounded-t-lg border-b-2 px-4 py-2.5 text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? "border-brand-600 bg-white text-brand-600 shadow-2xs font-semibold"
                  : "border-transparent text-slate-600 hover:border-slate-300 hover:text-slate-900"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <ReportFilters
        filters={filters}
        activeTab={activeTab}
        onFilterChange={handleFilterChange}
        onReset={handleResetFilters}
        onExportCsv={handleExportCsv}
        isExporting={isExporting}
        projects={projectOptions}
        members={memberOptions}
        customers={customerOptions}
      />

      {exportError && (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {exportError}
        </div>
      )}

      {activeTab === "project-performance" && (
        <div>
          {projectPerfQuery.isLoading ? (
            <LoadingState label="Loading project performance report..." />
          ) : projectPerfQuery.error ? (
            <ErrorState description="Failed to load project performance report." />
          ) : projectPerfQuery.data ? (
            <ProjectPerformanceReportView data={projectPerfQuery.data} />
          ) : null}
        </div>
      )}

      {activeTab === "team-workload" && (
        <div>
          {teamWorkloadQuery.isLoading ? (
            <LoadingState label="Loading team workload report..." />
          ) : teamWorkloadQuery.error ? (
            <ErrorState description="Failed to load team workload report." />
          ) : teamWorkloadQuery.data ? (
            <TeamWorkloadReportView data={teamWorkloadQuery.data} />
          ) : null}
        </div>
      )}

      {activeTab === "time" && (
        <div>
          {timeReportQuery.isLoading ? (
            <LoadingState label="Loading time tracking report..." />
          ) : timeReportQuery.error ? (
            <ErrorState description="Failed to load time report." />
          ) : timeReportQuery.data ? (
            <TimeReportView data={timeReportQuery.data} />
          ) : null}
        </div>
      )}

      {activeTab === "customer-overview" && (
        <div>
          {customerOverviewQuery.isLoading ? (
            <LoadingState label="Loading customer overview report..." />
          ) : customerOverviewQuery.error ? (
            <ErrorState description="Failed to load customer overview report." />
          ) : customerOverviewQuery.data ? (
            <CustomerOverviewReportView data={customerOverviewQuery.data} />
          ) : null}
        </div>
      )}
    </div>
  )
}
