import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router-dom"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { ReportsPage } from "../ReportsPage"
import { ProjectPerformanceReportView } from "@/features/reports/components/ProjectPerformanceReportView"
import * as authHook from "@/hooks/useAuth"
import * as reportsApi from "@/features/reports/api"
import * as projectsApi from "@/features/projects/api"
import * as teamApi from "@/features/team/api"
import * as customersApi from "@/features/customers/api"
import type {
  CustomerOverviewReport,
  ProjectPerformanceReport,
  TeamWorkloadReport,
  TimeReport,
} from "@/types/report"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/reports/api", () => ({
  fetchProjectPerformanceReport: vi.fn(),
  fetchTeamWorkloadReport: vi.fn(),
  fetchTimeReport: vi.fn(),
  fetchCustomerOverviewReport: vi.fn(),
  downloadReportCsv: vi.fn(),
}))

vi.mock("@/features/projects/api", () => ({
  fetchProjects: vi.fn(),
}))

vi.mock("@/features/team/api", () => ({
  fetchMembers: vi.fn(),
}))

vi.mock("@/features/customers/api", () => ({
  fetchCustomers: vi.fn(),
}))

const MOCK_COMPANY = {
  id: "comp-1",
  name: "Acme Corp",
  slug: "acme",
}

const MOCK_PROJECT_PERF: ProjectPerformanceReport = {
  summary: {
    total_projects: 2,
    total_tracked_hours: 12.5,
    average_progress: 65.0,
    total_tasks: 10,
    total_completed_tasks: 6,
    total_open_tasks: 4,
    total_overdue_tasks: 1,
  },
  status_distribution: [
    { status: "IN_PROGRESS", label: "In progress", count: 1 },
    { status: "COMPLETED", label: "Completed", count: 1 },
  ],
  results: [
    {
      project_id: "p1",
      project_name: "Cloud Migration",
      status: "IN_PROGRESS",
      status_label: "In progress",
      priority: "HIGH",
      progress: 60,
      completed_tasks: 3,
      open_tasks: 2,
      total_tasks: 5,
      overdue_tasks: 1,
      tracked_hours: 8.5,
      customer_id: "c1",
      customer_name: "Atlas Logistics",
      manager_name: "Sara Alami",
      start_date: "2025-05-01",
      deadline: "2025-07-01",
    },
    {
      project_id: "p2",
      project_name: "Portal Setup",
      status: "COMPLETED",
      status_label: "Completed",
      priority: "MEDIUM",
      progress: 100,
      completed_tasks: 3,
      open_tasks: 0,
      total_tasks: 3,
      overdue_tasks: 0,
      tracked_hours: 4.0,
      customer_id: "c2",
      customer_name: "Nova Retail",
      manager_name: "Youssef Benali",
      start_date: "2025-04-01",
      deadline: "2025-06-01",
    },
  ],
}

const MOCK_TEAM_WORKLOAD: TeamWorkloadReport = {
  summary: {
    total_members: 2,
    total_assigned_tasks: 8,
    total_open_tasks: 3,
    total_completed_tasks: 5,
    total_overdue_tasks: 1,
    total_tracked_hours: 14.5,
    overall_completion_rate: 63,
  },
  results: [
    {
      user_id: "u1",
      name: "Sara Alami",
      email: "sara@example.com",
      role: "ADMIN",
      assigned_tasks: 5,
      open_tasks: 2,
      completed_tasks: 3,
      overdue_tasks: 1,
      tracked_hours: 9.0,
      completion_rate: 60,
    },
    {
      user_id: "u2",
      name: "Youssef Benali",
      email: "youssef@example.com",
      role: "EMPLOYEE",
      assigned_tasks: 3,
      open_tasks: 1,
      completed_tasks: 2,
      overdue_tasks: 0,
      tracked_hours: 5.5,
      completion_rate: 67,
    },
  ],
}

const MOCK_TIME_REPORT: TimeReport = {
  summary: {
    total_hours: 18.0,
    total_entries: 6,
    active_projects_count: 2,
    active_users_count: 2,
    days_with_activity: 3,
    avg_daily_hours: 6.0,
  },
  hours_by_project: [
    {
      project_id: "p1",
      project_name: "Cloud Migration",
      customer_name: "Atlas Logistics",
      hours: 12.0,
      entry_count: 4,
      percentage: 66.7,
    },
    {
      project_id: "p2",
      project_name: "Portal Setup",
      customer_name: "Nova Retail",
      hours: 6.0,
      entry_count: 2,
      percentage: 33.3,
    },
  ],
  hours_by_user: [
    {
      user_id: "u1",
      user_name: "Sara Alami",
      email: "sara@example.com",
      hours: 10.0,
      entry_count: 3,
      percentage: 55.6,
    },
    {
      user_id: "u2",
      user_name: "Youssef Benali",
      email: "youssef@example.com",
      hours: 8.0,
      entry_count: 3,
      percentage: 44.4,
    },
  ],
  timeline: [
    { date: "2025-06-01", hours: 6.0, entry_count: 2 },
    { date: "2025-06-02", hours: 8.0, entry_count: 3 },
    { date: "2025-06-03", hours: 4.0, entry_count: 1 },
  ],
  entries: [
    {
      id: "e1",
      date: "2025-06-01",
      project_id: "p1",
      project_name: "Cloud Migration",
      user_id: "u1",
      user_name: "Sara Alami",
      task_id: "t1",
      task_title: "Setup VPC",
      duration_hours: 3.5,
      start_time: "09:00:00",
      end_time: "12:30:00",
      description: "Provisioned VPC",
    },
  ],
}

const MOCK_CUSTOMER_OVERVIEW: CustomerOverviewReport = {
  summary: {
    total_customers: 2,
    active_customers: 1,
    total_active_projects: 1,
    total_completed_projects: 1,
    total_tracked_hours: 12.5,
  },
  results: [
    {
      customer_id: "c1",
      customer_name: "Karim Idrissi",
      company_name: "Atlas Logistics",
      display_name: "Atlas Logistics",
      email: "contact@atlas.demo",
      phone: "+123",
      status: "ACTIVE",
      is_active: true,
      active_projects: 1,
      completed_projects: 0,
      total_projects: 1,
      open_tasks: 2,
      hours_tracked: 8.5,
    },
    {
      customer_id: "c2",
      customer_name: "Leila Moussaoui",
      company_name: "Nova Retail",
      display_name: "Nova Retail",
      email: "contact@nova.demo",
      phone: "+456",
      status: "ACTIVE",
      is_active: true,
      active_projects: 0,
      completed_projects: 1,
      total_projects: 1,
      open_tasks: 0,
      hours_tracked: 4.0,
    },
  ],
}

function renderReportsPage(initialRoute = "/reports") {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path="/reports" element={<ReportsPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("ReportsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(authHook.useAuth).mockReturnValue({
      activeCompany: MOCK_COMPANY,
      role: "ADMIN",
      user: { id: "u1", email: "admin@nexora.demo" },
    } as ReturnType<typeof authHook.useAuth>)

    vi.mocked(projectsApi.fetchProjects).mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [
        { id: "p1", name: "Cloud Migration" } as unknown as import("@/types/project").Project,
      ],
    })

    vi.mocked(teamApi.fetchMembers).mockResolvedValue([
      {
        id: "u1",
        email: "sara@example.com",
        full_name: "Sara Alami",
        first_name: "Sara",
        last_name: "Alami",
        role: "ADMIN",
        membership_id: "m1",
        membership_active: true,
        joined_at: null,
      },
    ])

    vi.mocked(customersApi.fetchCustomers).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [
        { id: "c1", name: "Karim Idrissi", company_name: "Atlas Logistics" } as unknown as import("@/types/customer").Customer,
      ],
    })

    vi.mocked(reportsApi.fetchProjectPerformanceReport).mockResolvedValue(MOCK_PROJECT_PERF)
    vi.mocked(reportsApi.fetchTeamWorkloadReport).mockResolvedValue(MOCK_TEAM_WORKLOAD)
    vi.mocked(reportsApi.fetchTimeReport).mockResolvedValue(MOCK_TIME_REPORT)
    vi.mocked(reportsApi.fetchCustomerOverviewReport).mockResolvedValue(MOCK_CUSTOMER_OVERVIEW)
  })

  it("renders ProjectPerformanceReportView directly", () => {
    render(
      <MemoryRouter>
        <ProjectPerformanceReportView data={MOCK_PROJECT_PERF} />
      </MemoryRouter>,
    )
    expect(screen.getByText("Total Projects")).toBeInTheDocument()
    expect(screen.getAllByText("Cloud Migration").length).toBeGreaterThan(0)
  })

  it("renders the page header and default project performance tab", async () => {
    renderReportsPage()

    expect(screen.getByText("Business Reports & Analytics")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Project Performance" })).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText("Total Projects")).toBeInTheDocument()
      expect(screen.getByText("12.5h")).toBeInTheDocument()
      expect(screen.getByText("65%")).toBeInTheDocument()
      expect(screen.getAllByText("Cloud Migration").length).toBeGreaterThan(0)
      expect(screen.getAllByText("Portal Setup").length).toBeGreaterThan(0)
    })
  })

  it("switches tabs to Team Workload and renders member workload metrics", async () => {
    const user = userEvent.setup()
    renderReportsPage()

    await waitFor(() => {
      expect(screen.getAllByText("Cloud Migration").length).toBeGreaterThan(0)
    })

    const teamTab = screen.getByText("Team Workload")
    await user.click(teamTab)

    await waitFor(() => {
      expect(screen.getByText("Active Members")).toBeInTheDocument()
      expect(screen.getAllByText("Sara Alami").length).toBeGreaterThan(0)
      expect(screen.getAllByText("Youssef Benali").length).toBeGreaterThan(0)
      expect(screen.getByText("14.5h")).toBeInTheDocument()
    })
  })

  it("switches tabs to Time Report and displays time summary and detailed logs", async () => {
    const user = userEvent.setup()
    renderReportsPage()

    const timeTab = screen.getByText("Time Report")
    await user.click(timeTab)

    await waitFor(() => {
      expect(screen.getByText("Total Logged Time")).toBeInTheDocument()
      expect(screen.getByText("18.0h")).toBeInTheDocument()
      expect(screen.getByText("Hours Breakdown Tables")).toBeInTheDocument()
      expect(screen.getByText("Detailed Time Entries Log (1)")).toBeInTheDocument()
    })

    const detailedTab = screen.getByText("Detailed Time Entries Log (1)")
    await user.click(detailedTab)

    await waitFor(() => {
      expect(screen.getByText("Provisioned VPC")).toBeInTheDocument()
    })
  })

  it("switches tabs to Customer Overview and displays portfolio data", async () => {
    const user = userEvent.setup()
    renderReportsPage()

    const customerTab = screen.getByText("Customer Overview")
    await user.click(customerTab)

    await waitFor(() => {
      expect(screen.getByText("Total Customers")).toBeInTheDocument()
      expect(screen.getByText("Active Engagements")).toBeInTheDocument()
      expect(screen.getAllByText("Atlas Logistics").length).toBeGreaterThan(0)
      expect(screen.getAllByText("Nova Retail").length).toBeGreaterThan(0)
    })
  })

  it("triggers CSV export when Export CSV button is clicked", async () => {
    const user = userEvent.setup()
    renderReportsPage()

    await waitFor(() => {
      expect(screen.getAllByText("Cloud Migration").length).toBeGreaterThan(0)
    })

    const exportBtn = screen.getByRole("button", { name: /export csv/i })
    await user.click(exportBtn)

    expect(reportsApi.downloadReportCsv).toHaveBeenCalledWith(
      "project-performance",
      expect.objectContaining({ date_from: "", date_to: "" }),
    )
  })

  it("triggers window.print when Print / PDF button is clicked", async () => {
    const printSpy = vi.spyOn(window, "print").mockImplementation(() => {})
    const user = userEvent.setup()
    renderReportsPage()

    await waitFor(() => {
      expect(screen.getAllByText("Cloud Migration").length).toBeGreaterThan(0)
    })

    const printBtn = screen.getByRole("button", { name: /print \/ pdf/i })
    await user.click(printBtn)

    expect(printSpy).toHaveBeenCalled()
    printSpy.mockRestore()
  })

  it("applies date presets and updates filter state", async () => {
    const user = userEvent.setup()
    renderReportsPage()

    await waitFor(() => {
      expect(screen.getAllByText("Cloud Migration").length).toBeGreaterThan(0)
    })

    const thirtyDaysBtn = screen.getByText("Last 30 days")
    await user.click(thirtyDaysBtn)

    await waitFor(() => {
      expect(screen.getByText("Reset all filters")).toBeInTheDocument()
    })

    await user.click(screen.getByText("Reset all filters"))
    await waitFor(() => {
      expect(screen.queryByText("Reset all filters")).not.toBeInTheDocument()
    })
  })
})
