import { api } from "@/services/api"
import type {
  CustomerOverviewReport,
  ExecutiveSummaryReport,
  ProjectPerformanceReport,
  ReportFilterParams,
  ReportType,
  TeamWorkloadReport,
  TimeReport,
} from "@/types/report"

export async function fetchProjectPerformanceReport(
  params: ReportFilterParams = {},
): Promise<ProjectPerformanceReport> {
  const { data } = await api.get<ProjectPerformanceReport>(
    "/reports/project-performance/",
    { params },
  )
  return data
}

export async function fetchTeamWorkloadReport(
  params: ReportFilterParams = {},
): Promise<TeamWorkloadReport> {
  const { data } = await api.get<TeamWorkloadReport>(
    "/reports/team-workload/",
    { params },
  )
  return data
}

export async function fetchTimeReport(
  params: ReportFilterParams = {},
): Promise<TimeReport> {
  const { data } = await api.get<TimeReport>("/reports/time/", { params })
  return data
}

export async function fetchCustomerOverviewReport(
  params: ReportFilterParams = {},
): Promise<CustomerOverviewReport> {
  const { data } = await api.get<CustomerOverviewReport>(
    "/reports/customer-overview/",
    { params },
  )
  return data
}

export async function fetchExecutiveSummary(
  params: ReportFilterParams = {},
): Promise<ExecutiveSummaryReport> {
  const { data } = await api.get<ExecutiveSummaryReport>(
    "/reports/summary/",
    { params },
  )
  return data
}

export async function downloadReportCsv(
  reportType: ReportType,
  params: ReportFilterParams = {},
  customFilename?: string,
): Promise<void> {
  const urlMap: Record<ReportType, string> = {
    "project-performance": "/reports/project-performance/export/",
    "team-workload": "/reports/team-workload/export/",
    time: "/reports/time/export/",
    "customer-overview": "/reports/customer-overview/export/",
  }

  const endpoint = urlMap[reportType]
  const response = await api.get(endpoint, {
    params,
    responseType: "blob",
  })

  let filename = customFilename || `${reportType}-report.csv`
  const disposition = response.headers?.["content-disposition"]
  if (disposition && typeof disposition === "string") {
    const match = disposition.match(/filename="?([^"]+)"?/)
    if (match && match[1]) {
      filename = match[1]
    }
  }

  const blob = new Blob([response.data], { type: "text/csv;charset=utf-8;" })
  const link = document.createElement("a")
  const url = window.URL.createObjectURL(blob)
  link.href = url
  link.setAttribute("download", filename)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
