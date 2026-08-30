import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

import { TimeTrackingPage } from "../TimeTrackingPage"
import * as authHook from "@/hooks/useAuth"
import * as timeTrackingApi from "@/features/time-tracking/api"
import * as projectsApi from "@/features/projects/api"
import * as tasksApi from "@/features/tasks/api"

vi.mock("@/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/features/time-tracking/api", () => ({
  fetchTimeEntries: vi.fn(),
  fetchTimeEntry: vi.fn(),
  createTimeEntry: vi.fn(),
  updateTimeEntry: vi.fn(),
  deleteTimeEntry: vi.fn(),
  fetchTimeEntrySummary: vi.fn(),
}))

vi.mock("@/features/projects/api", () => ({
  fetchProjects: vi.fn(),
}))

vi.mock("@/features/tasks/api", () => ({
  fetchAllTasks: vi.fn(),
}))

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
}

const MOCK_ENTRIES = [
  {
    id: "te1",
    user: "u1",
    user_name: "Admin Test",
    project: "p1",
    project_name: "Website Redesign",
    task: "t1",
    task_title: "Fix login bug",
    date: "2025-08-20",
    start_time: "09:00:00",
    end_time: "11:30:00",
    duration: "2:30:00",
    description: "Morning work",
    created_at: "2025-08-20T09:00:00Z",
    updated_at: "2025-08-20T11:30:00Z",
  },
  {
    id: "te2",
    user: "u1",
    user_name: "Admin Test",
    project: "p1",
    project_name: "Website Redesign",
    task: null,
    task_title: null,
    date: "2025-08-20",
    start_time: "14:00:00",
    end_time: "15:00:00",
    duration: "1:00:00",
    description: "Afternoon meeting",
    created_at: "2025-08-20T14:00:00Z",
    updated_at: "2025-08-20T15:00:00Z",
  },
  {
    id: "te3",
    user: "u1",
    user_name: "Admin Test",
    project: "p2",
    project_name: "Mobile App",
    task: null,
    task_title: null,
    date: "2025-08-19",
    start_time: "10:00:00",
    end_time: null,
    duration: null,
    description: "Still in progress",
    created_at: "2025-08-19T10:00:00Z",
    updated_at: "2025-08-19T10:00:00Z",
  },
]

const MOCK_SUMMARY = {
  total_entries: 3,
  total_duration_minutes: 210,
  by_project: [
    { project_name: "Website Redesign", total_minutes: 150 },
    { project_name: "Mobile App", total_minutes: 60 },
  ],
  by_date: [
    { date: "2025-08-20", total_minutes: 150 },
    { date: "2025-08-19", total_minutes: 60 },
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
          <TimeTrackingPage />
        </QueryClientProvider>
      </MemoryRouter>,
    ),
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockAuth()
  vi.mocked(timeTrackingApi.fetchTimeEntries).mockResolvedValue({
    count: MOCK_ENTRIES.length,
    next: null,
    previous: null,
    results: MOCK_ENTRIES,
  })
  vi.mocked(timeTrackingApi.fetchTimeEntrySummary).mockResolvedValue(MOCK_SUMMARY)
  vi.mocked(projectsApi.fetchProjects).mockResolvedValue({
    count: 0,
    next: null,
    previous: null,
    results: [],
  })
  vi.mocked(tasksApi.fetchAllTasks).mockResolvedValue({
    count: 0,
    next: null,
    previous: null,
    results: [],
  })
})

async function waitForData() {
  await waitFor(() => {
    expect(screen.getByText("Total This Period")).toBeInTheDocument()
  })
}

describe("TimeTrackingPage", () => {
  describe("rendering", () => {
    it("shows loading state", () => {
      vi.mocked(timeTrackingApi.fetchTimeEntries).mockReturnValue(new Promise(() => {}))
      renderPage()
      expect(screen.getByText(/Loading entries/i)).toBeInTheDocument()
    })

    it("renders entries in table", async () => {
      renderPage()
      await waitForData()
      expect(screen.getAllByText("Website Redesign").length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText("Mobile App").length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText("Fix login bug")).toBeInTheDocument()
    })

    it("shows summary cards", async () => {
      renderPage()
      await waitForData()
      expect(screen.getByText("Total This Period")).toBeInTheDocument()
      expect(screen.getByText("Today")).toBeInTheDocument()
      expect(screen.getByText("This Week")).toBeInTheDocument()
    })

    it("shows total duration in summary", async () => {
      renderPage()
      await waitForData()
      expect(screen.getByText("3h 30m")).toBeInTheDocument()
    })

    it("shows project breakdown", async () => {
      renderPage()
      await waitForData()
      expect(screen.getByText("Time by Project")).toBeInTheDocument()
      expect(screen.getAllByText("2h 30m").length).toBeGreaterThanOrEqual(1)
    })

    it("shows entry count in filter bar", async () => {
      renderPage()
      await waitForData()
      expect(screen.getAllByText(/3 entr/).length).toBeGreaterThanOrEqual(1)
    })

    it("shows error state on fetch failure", async () => {
      vi.mocked(timeTrackingApi.fetchTimeEntries).mockRejectedValue(new Error("Network"))
      renderPage()
      await waitFor(() => {
        expect(screen.getByText("Could not load time entries")).toBeInTheDocument()
      })
    })

    it("shows empty state when no entries", async () => {
      vi.mocked(timeTrackingApi.fetchTimeEntries).mockResolvedValue({
        count: 0,
        next: null,
        previous: null,
        results: [],
      })
      vi.mocked(timeTrackingApi.fetchTimeEntrySummary).mockResolvedValue({
        total_entries: 0,
        total_duration_minutes: 0,
        by_project: [],
        by_date: [],
      })
      renderPage()
      await waitFor(() => {
        expect(screen.getByText("No time entries")).toBeInTheDocument()
      })
    })

    it("shows running status for entries without end time", async () => {
      renderPage()
      await waitForData()
      expect(screen.getByText("Running")).toBeInTheDocument()
    })
  })

  describe("filters", () => {
    it("shows project filter and date inputs", async () => {
      renderPage()
      await waitForData()
      expect(screen.getByDisplayValue("All projects")).toBeInTheDocument()
    })

    it("project filter is interactive", async () => {
      vi.mocked(projectsApi.fetchProjects).mockResolvedValue({
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: "p1",
            name: "Website Redesign",
            description: "",
            customer: null,
            customer_name: null,
            manager: null,
            manager_name: null,
            status: "IN_PROGRESS",
            priority: "HIGH",
            start_date: null,
            deadline: null,
            created_at: "2025-01-01T00:00:00Z",
            updated_at: "2025-01-01T00:00:00Z",
          },
        ],
      })
      const user = userEvent.setup()
      renderPage()
      await waitForData()
      const select = screen.getByDisplayValue("All projects")
      await user.selectOptions(select, "p1")
      expect(select).toHaveValue("p1")
    })
  })

  describe("create entry", () => {
    it("opens log time modal", async () => {
      const user = userEvent.setup()
      renderPage()
      await waitForData()
      await user.click(screen.getByRole("button", { name: /log time/i }))
      expect(screen.getByRole("dialog")).toBeInTheDocument()
      expect(screen.getByText("Log time", { selector: "h2" })).toBeInTheDocument()
    })

    it("shows required form fields", async () => {
      const user = userEvent.setup()
      renderPage()
      await waitForData()
      await user.click(screen.getByRole("button", { name: /log time/i }))
      expect(screen.getByLabelText("Project")).toBeInTheDocument()
      expect(screen.getByLabelText("Date")).toBeInTheDocument()
      expect(screen.getByLabelText("Start time")).toBeInTheDocument()
    })
  })

  describe("edit entry", () => {
    it("opens edit modal with pre-filled data", async () => {
      const user = userEvent.setup()
      renderPage()
      await waitForData()
      const editButtons = screen.getAllByText("Edit")
      await user.click(editButtons[0])
      expect(screen.getByRole("dialog")).toBeInTheDocument()
      expect(screen.getByText("Edit time entry", { selector: "h2" })).toBeInTheDocument()
    })
  })

  describe("delete entry", () => {
    it("shows delete buttons for admin", async () => {
      renderPage()
      await waitForData()
      expect(screen.getAllByText("Delete").length).toBeGreaterThan(0)
    })

    it("opens delete confirmation modal", async () => {
      const user = userEvent.setup()
      renderPage()
      await waitForData()
      await user.click(screen.getAllByText("Delete")[0])
      expect(screen.getByText("Delete time entry", { selector: "h2" })).toBeInTheDocument()
    })
  })

  describe("permissions", () => {
    it("employee does not see delete buttons", async () => {
      mockAuth("EMPLOYEE")
      renderPage()
      await waitForData()
      expect(screen.queryByText("Delete")).not.toBeInTheDocument()
    })

    it("manager sees delete buttons", async () => {
      mockAuth("MANAGER")
      renderPage()
      await waitForData()
      expect(screen.getAllByText("Delete").length).toBeGreaterThan(0)
    })
  })
})
