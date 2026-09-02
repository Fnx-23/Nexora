import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { DashboardPage } from "../DashboardPage"
import * as authHook from "@/hooks/useAuth"
import * as dashboardApi from "@/features/dashboard/api"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/dashboard/api", () => ({
  fetchDashboard: vi.fn(),
}))

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
}

const MOCK_DASHBOARD = {
  kpis: {
    active_projects: 3,
    total_projects: 7,
    total_customers: 12,
    open_tasks: 15,
    overdue_tasks: 2,
    completed_tasks: 23,
    total_tasks: 38,
    team_members: 5,
  },
  project_status_distribution: [
    { status: "PLANNING", label: "Planning", count: 2 },
    { status: "IN_PROGRESS", label: "In Progress", count: 1 },
    { status: "COMPLETED", label: "Completed", count: 4 },
  ],
  task_status_distribution: [
    { status: "TODO", label: "To Do", count: 5 },
    { status: "IN_PROGRESS", label: "In Progress", count: 7 },
    { status: "IN_REVIEW", label: "In Review", count: 3 },
    { status: "DONE", label: "Done", count: 23 },
  ],
  recent_projects: [
    {
      id: "p1",
      name: "Website Redesign",
      status: "IN_PROGRESS",
      priority: "HIGH",
      deadline: "2025-09-30",
      updated_at: "2025-08-20T14:00:00Z",
    },
    {
      id: "p2",
      name: "Mobile App",
      status: "PLANNING",
      priority: "MEDIUM",
      deadline: null,
      updated_at: "2025-08-19T10:00:00Z",
    },
  ],
  recent_tasks: [
    {
      id: "t1",
      title: "Fix login bug",
      status: "IN_PROGRESS",
      priority: "URGENT",
      assignee_name: "Alice",
      due_date: "2025-08-25",
      updated_at: "2025-08-20T14:00:00Z",
    },
    {
      id: "t2",
      title: "Write API docs",
      status: "TODO",
      priority: "MEDIUM",
      assignee_name: null,
      due_date: null,
      updated_at: "2025-08-19T10:00:00Z",
    },
  ],
  activity: [
    {
      type: "project" as const,
      id: "p1",
      name: "Website Redesign",
      status: "IN_PROGRESS",
      updated_at: "2025-08-20T14:00:00Z",
    },
    {
      type: "task" as const,
      id: "t1",
      name: "Fix login bug",
      status: "IN_PROGRESS",
      updated_at: "2025-08-20T12:00:00Z",
    },
  ],
}

function mockAuth(role: "ADMIN" | "MANAGER" | "EMPLOYEE" = "ADMIN") {
  vi.mocked(authHook.useAuth).mockReturnValue({
    status: "authenticated",
    user: {
      id: "u1",
      email: "admin@test.com",
      first_name: "Admin",
      last_name: "Test",
      avatar: null,
      full_name: "Admin Test",
    },
    activeCompany: { id: "c1", name: "TestCo", slug: "testco" },
    role,
    login: vi.fn(),
    logout: vi.fn(),
    refreshSession: vi.fn(),
  })
}

function renderPage(queryClient?: QueryClient) {
  const qc = queryClient ?? makeQueryClient()
  return {
    qc,
    ...render(
      <MemoryRouter>
        <QueryClientProvider client={qc}>
          <DashboardPage />
        </QueryClientProvider>
      </MemoryRouter>,
    ),
  }
}

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuth()
  })

  it("shows welcome message with user's first name", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockResolvedValue(MOCK_DASHBOARD)
    renderPage()
    expect(screen.getByText(/Welcome back, Admin/)).toBeInTheDocument()
  })

  it("shows company name in description", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockResolvedValue(MOCK_DASHBOARD)
    renderPage()
    expect(screen.getByText(/You are working in TestCo/)).toBeInTheDocument()
  })

  it("renders KPI cards with correct values", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockResolvedValue(MOCK_DASHBOARD)
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("3")).toBeInTheDocument()
      expect(screen.getByText("7 total")).toBeInTheDocument()
      expect(screen.getByText("15")).toBeInTheDocument()
      expect(screen.getByText("2 overdue")).toBeInTheDocument()
      expect(screen.getByText("12")).toBeInTheDocument()
      expect(screen.getByText("5")).toBeInTheDocument()
    })
  })

  it("renders project status distribution", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockResolvedValue(MOCK_DASHBOARD)
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("Planning: 2")).toBeInTheDocument()
      expect(screen.getByText("In Progress: 1")).toBeInTheDocument()
      expect(screen.getByText("Completed: 4")).toBeInTheDocument()
    })
  })

  it("renders task status distribution", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockResolvedValue(MOCK_DASHBOARD)
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("To Do: 5")).toBeInTheDocument()
      expect(screen.getByText("In Progress: 7")).toBeInTheDocument()
      expect(screen.getByText("In Review: 3")).toBeInTheDocument()
      expect(screen.getByText("Done: 23")).toBeInTheDocument()
    })
  })

  it("renders recent projects with links", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockResolvedValue(MOCK_DASHBOARD)
    renderPage()
    await waitFor(() => {
      const links = screen.getAllByText("Website Redesign")
      expect(links.length).toBeGreaterThanOrEqual(1)
      const parentLink = links.find((el) => el.closest("a"))
      expect(parentLink).toBeDefined()
      expect(parentLink!.closest("a")).toHaveAttribute("href", "/projects/p1")
      expect(screen.getByText("Mobile App")).toBeInTheDocument()
    })
  })

  it("renders recent tasks", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockResolvedValue(MOCK_DASHBOARD)
    renderPage()
    await waitFor(() => {
      expect(screen.getAllByText("Fix login bug").length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText("Write API docs")).toBeInTheDocument()
    })
  })

  it("renders activity feed", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockResolvedValue(MOCK_DASHBOARD)
    renderPage()
    await waitFor(() => {
      expect(screen.getAllByText("Website Redesign").length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText("Fix login bug").length).toBeGreaterThanOrEqual(1)
    })
  })

  it("shows skeleton while loading", () => {
    vi.mocked(dashboardApi.fetchDashboard).mockReturnValue(new Promise(() => {}))
    renderPage()
    expect(screen.getByText(/Welcome back/)).toBeInTheDocument()
    const skeletons = document.querySelectorAll('[aria-hidden="true"]')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it("shows error state on fetch failure", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockRejectedValue(new Error("Network error"))
    renderPage()
    await waitFor(() => {
      expect(screen.getByText(/Failed to load dashboard data/)).toBeInTheDocument()
    })
  })

  it("shows empty states when no data", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockResolvedValue({
      ...MOCK_DASHBOARD,
      recent_projects: [],
      recent_tasks: [],
      activity: [],
    })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("No projects yet.")).toBeInTheDocument()
      expect(screen.getByText("No tasks yet.")).toBeInTheDocument()
      expect(screen.getByText("No activity yet.")).toBeInTheDocument()
    })
  })

  it("highlights overdue tasks in danger color", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockResolvedValue(MOCK_DASHBOARD)
    renderPage()
    await waitFor(() => {
      const hint = screen.getByText("2 overdue")
      expect(hint).toHaveClass("text-red-600")
    })
  })

  it("shows role in access sidebar", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockResolvedValue(MOCK_DASHBOARD)
    renderPage()
    expect(screen.getByText("Admin")).toBeInTheDocument()
  })

  it("recent cards allow shrinking to avoid horizontal overflow", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockResolvedValue(MOCK_DASHBOARD)
    renderPage()
    await waitFor(() => expect(screen.getByText("Recent Projects")).toBeInTheDocument())

    const recentHeading = screen.getByText("Recent Projects")
    expect(recentHeading.closest("[class*='rounded-2xl']") ?? recentHeading.closest("[class*='rounded-xl']")).toHaveClass("min-w-0")

    const tasksHeading = screen.getByText("Recent Tasks")
    expect(tasksHeading.closest("[class*='rounded-2xl']") ?? tasksHeading.closest("[class*='rounded-xl']")).toHaveClass("min-w-0")

    const activityHeading = screen.getByText("Recent Activity")
    expect(activityHeading.closest("[class*='rounded-2xl']") ?? activityHeading.closest("[class*='rounded-xl']")).toHaveClass("min-w-0")
  })

  it("shows zero-overdue hint when no overdue tasks", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockResolvedValue({
      ...MOCK_DASHBOARD,
      kpis: { ...MOCK_DASHBOARD.kpis, overdue_tasks: 0 },
    })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("No overdue")).toBeInTheDocument()
    })
  })

  it("handles zero totals in status distribution", async () => {
    vi.mocked(dashboardApi.fetchDashboard).mockResolvedValue({
      ...MOCK_DASHBOARD,
      project_status_distribution: [
        { status: "PLANNING", label: "Planning", count: 0 },
        { status: "IN_PROGRESS", label: "In Progress", count: 0 },
        { status: "COMPLETED", label: "Completed", count: 0 },
      ],
    })
    renderPage()
    await waitFor(() => {
      expect(screen.getByText("No data.")).toBeInTheDocument()
    })
  })
})
